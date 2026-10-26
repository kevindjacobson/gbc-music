/* music.c -- four-channel tracker-style music driver, see music.h for the data format.
 *
 * Register facts (pandocs): pulse tone = 131072 / (2048 - period) Hz, the wave channel plays the same
 * period one octave lower (65536 / (2048 - period)), so wave notes look up period(note + 12). NRx3/NRx4
 * written without bit 7 change the pitch without re-striking (arpeggios, vibrato, slides, glides click-free);
 * NRx1 duty bits can be rewritten any time without re-striking (duty sequences); NRx2 only takes effect on a
 * trigger, so pulse volume changes (FX_VOL, tremolo) come with a re-strike; NR32 on the wave channel does
 * not (level steps are the wave channel's click-free dynamics). Wave RAM can only be rewritten with NR30 = 0
 * (the channel's DAC off) and the channel must then be re-triggered. The driver never touches NR50/NR52
 * (sfx_init owns them); NR51 (panning) it owns through a shadow byte (music_set_pan_base & the music's pans, see
 * music.h), written only when the value changes. It never uses the hardware sweep NR10 (pulse 1 only, keeps running
 * across notes, fights re-triggers): every pitch movement here is software on NRx3/NRx4, which all four tonal uses share.
 *
 * Cost: music_tick is a few hundred cycles on a quiet frame and about 1.5k-3k cycles when all four channels
 * move (the measured figure is in research_notes/gb-timbre-modulation); the wave-table step (16-byte copy)
 * is the one expensive event and only happens on wave-sequence instruments.
 */
#include <gb/gb.h>
#include <gb/hardware.h>
#include "music.h"

#define NCH 4
#define TABLE_BASE 36                /* MIDI note of period_table[0] (C2, 65 Hz, the lowest pulse note) */
#define TABLE_LEN 72
#define RING 16                      /* echo history (frames); FX_ECHO delay is 1..15 */

static const uint16_t period_table[TABLE_LEN] = {
      44,  156,  262,  363,  457,  547,  631,  710,  786,  854,  923,  986,   /* C2..B2  (MIDI 36..47) */
    1046, 1102, 1155, 1205, 1253, 1297, 1339, 1379, 1417, 1452, 1486, 1517,   /* C3..B3  (48..59) */
    1546, 1575, 1602, 1627, 1650, 1673, 1694, 1714, 1732, 1750, 1767, 1783,   /* C4..B4  (60..71) */
    1798, 1812, 1825, 1837, 1849, 1860, 1871, 1881, 1890, 1899, 1907, 1915,   /* C5..B5  (72..83) */
    1923, 1930, 1936, 1943, 1949, 1954, 1959, 1964, 1969, 1974, 1978, 1982,   /* C6..B6  (84..95) */
    1985, 1989, 1992, 1995, 1998, 2001, 2004, 2006, 2009, 2011, 2013, 2015    /* C7..B7  (96..107) */
};

typedef struct {
    uint8_t note;      /* base MIDI note being held, 0 = silent */
    uint8_t inst;      /* current instrument index (0-based) */
    uint8_t vol;       /* 0..15 volume of the current note before master scaling */
    uint8_t hwvol;     /* volume last written to the hardware (tremolo compares against it) */
    uint8_t fx;
    uint8_t param;
    uint8_t arp_idx;   /* chord slot */
    uint8_t arp_t;     /* frames until the next chord slot */
    uint8_t vib_phase;
    uint8_t held;      /* frames the note has been held (saturates) */
    uint8_t hold;      /* frames an SFX still owns this channel */
    uint8_t cut;       /* frames until a FX_CUT silences the note (0 = none) */
    uint8_t stack;     /* noise: second drum (1..15) to strike when stack_t reaches 0 */
    uint8_t stack_t;
    uint8_t stage;     /* noise: drum whose second stage fires when stage_t reaches 0 (1..15, 0 = none) */
    uint8_t stage_t;
    uint8_t sounding;  /* a note is on the hardware */
    uint8_t seq_i;     /* duty-sequence / wave-sequence position */
    uint8_t seq_t;     /* frames until the next sequence step */
    uint8_t seq_done;  /* wave one-shot sequence finished */
    uint8_t wl;        /* wave: current NR32 level code 1 (full) .. 3 (quarter) */
    uint8_t wenv_t;    /* wave: frames until the next level step */
    uint8_t apan_t;    /* pulse: frames until the instrument's auto-pan flips side */
    uint8_t gl_rem;    /* glide (bend / portamento / pitch envelope): frames left */
    int16_t gl_cur;    /* glide: current period offset, reaches 0 when the glide lands */
    int16_t gl_step;   /* glide: per-frame change of gl_cur */
    int16_t slide;     /* accumulated FX_SLIDE period offset */
    uint16_t period;   /* last period written */
} Chan;

typedef struct {
    uint16_t period;
    uint8_t vol;       /* 0 = ch1 silent this frame */
    uint8_t trig;
} RingSlot;

static const Song *song;
static Chan ch[NCH];
static uint8_t order_i, row_i, row_frame;
static uint8_t arp_speed;
static uint8_t mvol = 15;
static uint8_t echo;               /* ch2 FX_ECHO param, 0 = off */
static uint8_t frame_i;
static RingSlot ring[RING];
static uint8_t cur_wave = 0xFF;    /* wave shape currently in wave RAM */
static uint8_t pan_base = 0xFF;    /* the game's NR51 mask (music_set_pan_base) */
static uint8_t pan_music = 0xFF;   /* the music's own pans, NR51 layout (bits 0-3 right, 4-7 left) */
static uint8_t pan_last;           /* NR51 value last written by the driver (0 = never) */
static uint8_t pan_dirty;          /* the shadow changed: write NR51 at the end of the tick */
static uint8_t echo_side;          /* the echo cell set pulse 2's side: put it back to both when the echo ends */
static uint8_t pan_ch[2];          /* current side of each pulse channel (MUSIC_PAN_R / L / C) */
static const uint8_t PAN_BITS[2][4] = { { 0x00, 0x01, 0x10, 0x11 }, { 0x00, 0x02, 0x20, 0x22 } };   /* [channel][side] -> NR51 bits */
static const uint8_t HOLD_BITS[NCH] = { 0x11, 0x22, 0x44, 0x88 };

/* ---- register helpers ---------------------------------------------------------------------------- */

/* NR51 = base & music pans; a channel held by an SFX keeps the bits the SFX left in the register. One write, and
 * only when the value differs from the last one written (the probe counts every write as a pan event). */
static void pan_apply(void) {
    uint8_t v = (uint8_t)(pan_base & pan_music);
    uint8_t held = 0, c;
    for (c = 0; c != NCH; c++) if (ch[c].hold) held |= HOLD_BITS[c];
    if (held) v = (uint8_t)((uint8_t)(v & (uint8_t)~held) | (uint8_t)(NR51_REG & held));
    pan_dirty = 0;
    if (v != pan_last) { NR51_REG = v; pan_last = v; }
}

/* Pulse channel c (0 or 1) to `side` (MUSIC_PAN_R / L / C) in the music's pans; NR51 follows at the end of the tick. */
static void set_pan(uint8_t c, uint8_t side) {
    pan_ch[c] = side;
    pan_music = (uint8_t)((uint8_t)(pan_music & (uint8_t)~PAN_BITS[c][3]) | PAN_BITS[c][side]);
    pan_dirty = 1;
}

static uint8_t scaled(uint8_t v) {
    return (uint8_t)(((uint8_t)(v * (uint8_t)(mvol + 1))) >> 4);
}

/* NRx2 for a pulse/noise channel: instrument envelope with its volume nibble replaced. */
static uint8_t env_byte(uint8_t env, uint8_t vol) {
    return (uint8_t)((uint8_t)(scaled(vol) << 4) | (uint8_t)(env & 0x0F));
}

/* 0..15 -> NR32 level code: 0 off, 1-4 quarter (3), 5-9 half (2), 10-15 full (1) */
static uint8_t wave_level(uint8_t vol) {
    uint8_t level = scaled(vol);
    return (uint8_t)(level == 0 ? 0 : (level < 5 ? 3 : (level < 10 ? 2 : 1)));
}

static void silence(uint8_t c) {
    switch (c) {
        case 0: NR12_REG = 0x08; NR14_REG = 0x80; break;
        case 1: NR22_REG = 0x08; NR24_REG = 0x80; break;
        case 2: NR30_REG = 0x00; break;
        default: NR42_REG = 0x08; NR44_REG = 0x80; break;
    }
    ch[c].sounding = 0;
}

static void write_period(uint8_t c, uint16_t p, uint8_t trig) {
    uint8_t hi = (uint8_t)((uint8_t)(p >> 8) & 0x07);
    if (trig) hi |= 0x80;
    switch (c) {
        case 0: NR13_REG = (uint8_t)p; NR14_REG = hi; break;
        case 1: NR23_REG = (uint8_t)p; NR24_REG = hi; break;
        default: NR33_REG = (uint8_t)p; NR34_REG = hi; break;
    }
    ch[c].period = p;
}

static void write_duty(uint8_t c, uint8_t duty) {
    if (c == 0) NR11_REG = duty; else NR21_REG = duty;
}

/* Current duty bits of a pulse instrument: the sequence slot if it has one, else the static duty. */
static uint8_t inst_duty(const Instrument *in, uint8_t slot) {
    if (in->mod & 0x07) return (uint8_t)((uint8_t)(in->seq << (uint8_t)(slot << 1)) & 0xC0);
    return (uint8_t)(in->duty & 0xC0);
}

static void load_wave(uint8_t w) {
    const uint8_t *src = song->waves + (uint8_t)(w << 4);
    uint8_t i;
    NR30_REG = 0x00;
    for (i = 0; i != 16; i++) AUD3WAVE[i] = src[i];
    NR30_REG = 0x80;
    cur_wave = w;
}

/* Strike channel c at `p` with its current instrument and volume. */
static void strike(uint8_t c, uint16_t p) {
    Chan *k = &ch[c];
    const Instrument *in = &song->instruments[k->inst];
    if (c == 0) {
        NR10_REG = 0x00;                        /* no hardware sweep: SFX may have left one */
        NR11_REG = inst_duty(in, k->seq_i);
        NR12_REG = env_byte(in->env, k->vol);
    } else if (c == 1) {
        NR21_REG = inst_duty(in, k->seq_i);
        NR22_REG = env_byte(in->env, k->vol);
    } else {
        uint8_t w = (uint8_t)(in->wave + k->seq_i);
        if (w != cur_wave) load_wave(w);
        else NR30_REG = 0x80;
        if (in->wenv & 0x80) k->wl = 3;         /* swell starts at quarter */
        else k->wl = wave_level(k->vol);
        k->wenv_t = (uint8_t)(in->wenv & 0x7F);
        NR32_REG = (uint8_t)(k->wl << 5);
    }
    k->hwvol = k->vol;
    write_period(c, p, 1);
    k->sounding = 1;
}

static void strike_noise(uint8_t env, uint8_t poly) {
    NR41_REG = 0x00;
    NR42_REG = env_byte(env, (uint8_t)(env >> 4));
    NR43_REG = poly;
    NR44_REG = 0x80;
    ch[3].sounding = 1;
}

static void strike_drum(uint8_t d) {
    const Drum *dr = &song->drums[(uint8_t)(d - 1)];
    strike_noise(dr->env, dr->poly);
    if (dr->env2) { ch[3].stage = d; ch[3].stage_t = MUSIC_DRUM_STAGE_FRAMES; }
    else ch[3].stage = 0;
}

static uint16_t period_of(uint8_t c, uint8_t note) {
    int8_t idx = (int8_t)((int8_t)note - (int8_t)TABLE_BASE);
    if (c == 2) idx = (int8_t)(idx + 12);     /* wave channel sounds an octave below the pulse table */
    if (idx < 0) idx = 0;
    if (idx >= TABLE_LEN) idx = TABLE_LEN - 1;
    return period_table[(uint8_t)idx];
}

/* ---- row reading --------------------------------------------------------------------------------- */

/* Start a glide that lands on `target` from `from`, over n frames (one division per note, none per frame). */
static void start_glide(Chan *k, uint16_t from, uint16_t target, uint8_t n) {
    int16_t d = (int16_t)((int16_t)from - (int16_t)target);
    if (n == 0) n = 1;
    k->gl_cur = d;
    k->gl_step = (int16_t)(-(d / (int16_t)n));
    k->gl_rem = n;
}

static void note_on(uint8_t c, uint8_t note) {
    Chan *k = &ch[c];
    const Instrument *in = &song->instruments[k->inst];
    uint16_t target = period_of(c, note);
    uint16_t prev = k->period;
    uint8_t had_note = k->note;
    k->note = note;
    k->held = 0;
    k->arp_idx = 0;
    k->arp_t = arp_speed;
    k->vib_phase = 0;
    k->slide = 0;
    k->cut = 0;
    k->gl_rem = 0;
    k->gl_cur = 0;
    if (c == 2) { k->seq_i = 0; k->seq_t = (uint8_t)(in->mod & 0x07); k->seq_done = 0; }   /* a wave sequence restarts per note; pulse duty sequences keep rotating */
    else if (in->wave) {                                 /* pulse instrument pan: a side per note, or an auto-pan that starts left */
        if (in->wave & 0x03) set_pan(c, (uint8_t)(in->wave & 0x03));
        k->apan_t = (uint8_t)(in->wave >> 2);
        if (k->apan_t) set_pan(c, MUSIC_PAN_L);
    }
    if (k->fx == MUSIC_FX_BEND) {
        uint8_t n = (uint8_t)(k->param >> 4);
        int8_t so = (int8_t)(k->param & 0x0F);
        if (so > 7) so = (int8_t)(so - 16);
        if (n) start_glide(k, period_of(c, (uint8_t)((int8_t)note + so)), target, n);
    } else if (k->fx == MUSIC_FX_PORTA) {
        if (had_note && prev && k->param) start_glide(k, prev, target, k->param);
    } else if (in->penv) {
        start_glide(k, period_of(c, (uint8_t)(note + (uint8_t)(in->penv >> 4))), target, (uint8_t)(in->penv & 0x0F));
    }
}

static void read_row(void) {
    uint8_t c;
    for (c = 0; c != NCH; c++) {
        Chan *k = &ch[c];
        const uint8_t *cell = song->patterns[song->orders[c][order_i]] + (uint8_t)(row_i * 3);
        uint8_t note = cell[0];
        uint8_t inst = (uint8_t)(cell[1] >> 4);
        uint8_t fx = (uint8_t)(cell[1] & 0x0F);
        uint8_t param = cell[2];
        uint8_t trig = 0;
        uint8_t pan = 0;

        if (c < 2 && (note & MUSIC_PAN_NOTE) && note != MUSIC_OFF) { pan = (uint8_t)(note & 0x03); note = 0; }   /* pan pseudo-note (pulse lanes; a drum stack also uses bit 7) */
        if (fx == MUSIC_FX_PAN) pan = (uint8_t)(param & 0x03);
        if (inst) {
            k->inst = (uint8_t)(inst - 1);
            k->vol = (uint8_t)(song->instruments[k->inst].env >> 4);
        }
        if (note || fx) { k->fx = fx; k->param = param; }
        if (fx == MUSIC_FX_VOL) k->vol = (uint8_t)(param & 0x0F);
        if (fx == MUSIC_FX_ARPSPEED && param) arp_speed = param;
        if (fx == MUSIC_FX_ECHO && c == 1) {
            echo = param;
            k->note = 0;
            if (!param && !k->hold) silence(c);
            if (echo_side && !param) { set_pan(1, MUSIC_PAN_C); echo_side = 0; }   /* the echo's side ends with the echo */
            if (param && pan) echo_side = 1;
        }
        if (fx == MUSIC_FX_CUT) k->cut = (uint8_t)(param ? param : 1);

        if (note == MUSIC_OFF) {
            k->note = 0;
            k->stack = 0;
            if (!k->hold) silence(c);
        } else if (note) {
            if (c == 3) {
                uint8_t d = (uint8_t)(note & 0x0F);
                k->stack = (uint8_t)(note >> 4);
                k->stack_t = MUSIC_STACK_FRAMES;
                k->note = d;
                if (d && !k->hold) strike_drum(d);
            } else {
                if (c == 1 && echo) {           /* a real ch2 note ends echo mode (and its side) */
                    echo = 0;
                    if (echo_side) { set_pan(1, MUSIC_PAN_C); echo_side = 0; }
                }
                note_on(c, note);
                trig = 1;
            }
        }
        if (pan && c < 2) set_pan(c, pan);      /* the cell's own pan wins over the instrument's */
        if (trig && !k->hold) strike(c, period_of(c, note));
    }
}

static void advance_row(void) {
    row_frame = 0;
    row_i++;
    if (row_i >= song->rows_per_pattern) {
        row_i = 0;
        order_i++;
        if (order_i >= song->n_orders) order_i = song->loop_to;
    }
}

/* ---- per-frame channel update -------------------------------------------------------------------- */

static int8_t tri8(uint8_t phase) {   /* 0..15 -> -4..4 triangle */
    uint8_t q = (uint8_t)(phase & 0x0F);
    int8_t v = (int8_t)(q < 8 ? q : (uint8_t)(16 - q));
    return (int8_t)(v - 4);
}

/* Tonal channels 0..2: compute this frame's pitch; returns the period and sets *trig when a re-strike is due. */
static uint16_t tonal_period(uint8_t c, uint8_t *trig) {
    Chan *k = &ch[c];
    const Instrument *in = &song->instruments[k->inst];
    uint8_t note = k->note;
    uint16_t p;
    int16_t off;
    uint8_t depth = 0, rate = 4;

    *trig = 0;
    switch (k->fx) {
        case MUSIC_FX_ARP: {
            const uint8_t *chord = song->chords + (uint8_t)(k->param << 2);
            uint8_t iv;
            if (k->arp_t == 0) {
                k->arp_t = arp_speed;
                k->arp_idx++;
                if (k->arp_idx > 3 || chord[k->arp_idx] == 0xFF) k->arp_idx = 0;
            }
            k->arp_t--;
            iv = chord[k->arp_idx];
            if (iv != 0xFF) note = (uint8_t)(note + iv);
            break;
        }
        case MUSIC_FX_TRILL: {
            uint8_t span = (uint8_t)(k->param >> 4);
            if ((span == 0 || row_frame < span) && (row_frame & 1)) note = (uint8_t)(note + (uint8_t)(k->param & 0x0F));
            break;
        }
        case MUSIC_FX_SPLIT:
            if (row_frame >= (uint8_t)(song->frames_per_row >> 1)) {
                note = k->param;
                if (row_frame == (uint8_t)(song->frames_per_row >> 1)) { *trig = 1; k->held = 0; }
            }
            break;
        case MUSIC_FX_VIB:
            depth = (uint8_t)(k->param >> 4);
            rate = (uint8_t)(k->param & 0x0F);
            break;
        case MUSIC_FX_SLIDE:
            k->slide = (int16_t)(k->slide + (int8_t)k->param);
            break;
        default: break;
    }
    if (depth == 0 && in->vib) {                 /* instrument auto-vibrato after its delay */
        uint8_t delay = (uint8_t)((uint8_t)(in->vib & 0x0F) << 2);
        if (k->held >= delay) { depth = (uint8_t)(in->vib >> 4); rate = 3; }
    }
    off = k->slide;
    if (depth) {
        if (rate == 0) rate = 1;
        if ((uint8_t)(k->held % rate) == 0) k->vib_phase++;
        off = (int16_t)(off + (int16_t)tri8(k->vib_phase) * (int16_t)depth);
    }
    if (k->gl_rem) {                             /* bend / portamento / pitch envelope: land, then hold */
        off = (int16_t)(off + k->gl_cur);
        k->gl_rem--;
        k->gl_cur = k->gl_rem ? (int16_t)(k->gl_cur + k->gl_step) : 0;
    }
    if (in->mod & 0xF0) {                        /* detune: signed nibble in period units */
        int8_t dt = (int8_t)(in->mod >> 4);
        if (dt > 7) dt = (int8_t)(dt - 16);
        off = (int16_t)(off + dt);
    }
    p = period_of(c, note);
    if (off < 0 && (uint16_t)(-off) > p) p = 0;
    else {
        p = (uint16_t)(p + off);
        if (p > 2047) p = 2047;
    }
    return p;
}

/* Instrument-level timbre motion for a sounding tonal channel: duty / wave sequences, wave level envelope, tremolo. */
static void update_timbre(uint8_t c) {
    Chan *k = &ch[c];
    const Instrument *in = &song->instruments[k->inst];
    uint8_t rate = (uint8_t)(in->mod & 0x07);
    if (c != 2 && (in->wave & 0xFC)) {           /* pulse auto-pan: flip the side every (wave >> 2) frames */
        if (k->apan_t > 1) k->apan_t--;
        else { k->apan_t = (uint8_t)(in->wave >> 2); set_pan(c, (uint8_t)(pan_ch[c] == MUSIC_PAN_L ? MUSIC_PAN_R : MUSIC_PAN_L)); }
    }
    if (rate && !(c == 2 && k->seq_done)) {
        if (k->seq_t) k->seq_t--;
        else {
            k->seq_t = (uint8_t)(rate - 1);
            if (c == 2) {
                if (k->seq_i < in->seq) k->seq_i++;
                else if (in->mod & 0x08) k->seq_i = 0;
                else { k->seq_done = 1; return; }
                load_wave((uint8_t)(in->wave + k->seq_i));
                write_period(c, k->period, 1);
            } else {
                k->seq_i = (uint8_t)((uint8_t)(k->seq_i + 1) & 3);
                write_duty(c, inst_duty(in, k->seq_i));
            }
        }
    }
    if (c == 2 && (in->wenv & 0x7F)) {           /* wave level envelope: NR32 steps, no re-trigger */
        if (k->wenv_t) k->wenv_t--;
        else {
            k->wenv_t = (uint8_t)((in->wenv & 0x7F) - 1);
            if (in->wenv & 0x80) { if (k->wl > 1) { k->wl--; NR32_REG = (uint8_t)(k->wl << 5); } }
            else if (k->wl < 3) { k->wl++; NR32_REG = (uint8_t)(k->wl << 5); }
            else { k->note = 0; silence(c); }
        }
    } else if (k->fx == MUSIC_FX_TREM) {         /* tremolo: dip every `rate` frames; a level step on wave, a re-strike on pulses */
        uint8_t tr = (uint8_t)(k->param & 0x0F);
        uint8_t dep = (uint8_t)(k->param >> 4);
        uint8_t want = k->vol;
        if (tr == 0) tr = 1;
        if ((uint8_t)(k->held / tr) & 1) want = (uint8_t)(dep >= want ? 0 : want - dep);
        if (want != k->hwvol) {
            k->hwvol = want;
            if (c == 2) { k->wl = wave_level(want); NR32_REG = (uint8_t)(k->wl << 5); }
            else {
                if (c == 0) NR12_REG = env_byte(in->env, want); else NR22_REG = env_byte(in->env, want);
                write_period(c, k->period, 1);
            }
        }
    }
}

static void update_tonal(uint8_t c) {
    Chan *k = &ch[c];
    uint16_t p;
    uint8_t trig;

    if (c == 1 && echo) {                        /* ch2 replays ch1 from the ring buffer */
        RingSlot *s = &ring[(uint8_t)((uint8_t)(frame_i - (uint8_t)(echo >> 4)) & (RING - 1))];
        uint8_t drop = (uint8_t)(echo & 0x0F);
        if (k->hold) return;
        if (!s->vol) { if (k->sounding) silence(c); return; }
        if (s->trig || !k->sounding) {
            k->inst = ch[0].inst;
            k->vol = (uint8_t)(s->vol > drop ? s->vol - drop : 0);
            strike(c, s->period);
        } else if (s->period != k->period) write_period(c, s->period, 0);
        return;
    }
    if (!k->note) {
        if (c == 0) { RingSlot *s = &ring[(uint8_t)(frame_i & (RING - 1))]; s->vol = 0; s->trig = 0; }
        return;
    }
    if (k->cut) {
        k->cut--;
        if (k->cut == 0) {
            k->note = 0;
            if (!k->hold) silence(c);
            if (c == 0) { RingSlot *s = &ring[(uint8_t)(frame_i & (RING - 1))]; s->vol = 0; s->trig = 0; }
            return;
        }
    }
    p = tonal_period(c, &trig);
    if (c == 0) {                                /* record for the echo voice */
        RingSlot *s = &ring[(uint8_t)(frame_i & (RING - 1))];
        s->period = p; s->vol = k->vol; s->trig = (uint8_t)(trig || k->held == 0);
    }
    if (!k->hold) {
        if (trig) strike(c, p);
        else if (p != k->period) write_period(c, p, 0);
        if (k->held) update_timbre(c);           /* from the second frame on: the strike itself set frame 0 */
    }
    if (k->held != 255) k->held++;
}

static void update_noise(void) {
    Chan *k = &ch[3];
    if (k->stage) {
        if (k->stage_t == 0) {
            const Drum *dr = &song->drums[(uint8_t)(k->stage - 1)];
            if (!k->hold) strike_noise(dr->env2, dr->poly2);
            k->stage = 0;
        } else k->stage_t--;
    }
    if (k->stack) {
        if (k->stack_t == 0) {
            if (!k->hold) strike_drum(k->stack);
            k->stack = 0;
        } else k->stack_t--;
    }
}

/* ---- public API ---------------------------------------------------------------------------------- */

void music_init(const Song *s) {
    uint8_t c;
    song = 0;
    for (c = 0; c != NCH; c++) {
        Chan *k = &ch[c];
        if (k->sounding) silence(c);
        k->note = 0; k->inst = 0; k->vol = 15; k->hwvol = 15; k->fx = 0; k->param = 0;
        k->arp_idx = 0; k->arp_t = 0; k->vib_phase = 0; k->held = 0; k->hold = 0; k->cut = 0;
        k->stack = 0; k->stack_t = 0; k->stage = 0; k->stage_t = 0; k->sounding = 0;
        k->seq_i = 0; k->seq_t = 0; k->seq_done = 0; k->wl = 1; k->wenv_t = 0; k->apan_t = 0;
        k->gl_rem = 0; k->gl_cur = 0; k->gl_step = 0; k->slide = 0; k->period = 0;
    }
    for (c = 0; c != RING; c++) { ring[c].vol = 0; ring[c].trig = 0; ring[c].period = 0; }
    echo = 0;
    echo_side = 0;
    pan_music = 0xFF;                            /* every channel back to both outputs */
    pan_ch[0] = MUSIC_PAN_C; pan_ch[1] = MUSIC_PAN_C;
    pan_apply();
    order_i = 0; row_i = 0; row_frame = 0; frame_i = 0;
    cur_wave = 0xFF;
    if (!s) return;
    song = s;
    arp_speed = s->arp_speed ? s->arp_speed : 3;
}

void music_stop(void) {
    uint8_t c;
    for (c = 0; c != NCH; c++) silence(c);
    song = 0;
    echo = 0;
    echo_side = 0;
    pan_music = 0xFF;
    pan_ch[0] = MUSIC_PAN_C; pan_ch[1] = MUSIC_PAN_C;
    pan_apply();
}

void music_set_pan_base(uint8_t mask) {
    pan_base = mask;
    pan_apply();
}

void music_set_volume(uint8_t vol) {
    mvol = (uint8_t)(vol > 15 ? 15 : vol);
}

uint8_t music_playing(void) { return (uint8_t)(song != 0); }
uint8_t music_bar(void) { return order_i; }
uint8_t music_row(void) { return row_i; }

void music_sfx(uint8_t channels, uint8_t frames) {
    uint8_t c;
    for (c = 0; c != NCH; c++)
        if ((channels & (uint8_t)(1 << c)) && ch[c].hold < frames) ch[c].hold = frames;
}

void music_tick(void) {
    uint8_t c;
    if (!song) return;
    /* SFX holds: when one runs out, re-strike the note the SFX talked over */
    for (c = 0; c != NCH; c++) {
        Chan *k = &ch[c];
        if (k->hold) {
            k->hold--;
            if (k->hold == 0) {
                pan_last = NR51_REG;             /* the SFX may have written NR51: put the shadow back */
                pan_dirty = 1;
                if (c == 3) { k->sounding = 0; }
                else if (c == 1 && echo) { k->sounding = 0; }
                else if (k->note) { if (c == 2) cur_wave = 0xFF; strike(c, k->period); }
                else silence(c);
            }
        }
    }
    if (row_frame == 0) read_row();
    update_tonal(0);
    update_tonal(1);
    update_tonal(2);
    update_noise();
    if (pan_dirty) pan_apply();
    row_frame++;
    if (row_frame >= song->frames_per_row) advance_row();
    frame_i++;
}
