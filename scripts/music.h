/* music.h -- four-channel background-music driver (pulse1 lead, pulse2 arpeggio/echo, wave bass, noise drums).
 *
 * Song data is ROM tables written by scripts/compose.py (src/music_data.c): orders -> patterns -> rows.
 * Every row is 16th-note sized (Song.frames_per_row frames); a pattern is one bar; each channel has its
 * own order list so repeated bars cost nothing. Call music_tick() once per frame, right after
 * wait_vbl_done(). SFX borrow channels through music_sfx(): the driver stops writing a borrowed
 * channel and re-strikes its note when the hold expires (sfx.c already does this for its five effects).
 *
 * Cell = 3 bytes per channel per row: [note][inst<<4 | fx][param]
 *   note   0 = nothing (continue), 1..127 = MIDI note (C-4 = 60), MUSIC_OFF = key off.
 *          0x80 | side (0x81 right, 0x82 left, 0x83 both; pulse lanes): a pan change on an effect-only cell
 *          (MUSIC_PAN_NOTE); the cell's fx / param still apply, the held note keeps sounding.
 *          Noise channel: low nibble = drum 1..15 (index + 1 into Song.drums), high nibble = a second
 *          drum re-struck MUSIC_STACK_FRAMES later (a kick+hat / snare+hat "stack").
 *   inst   0 = keep the current instrument, 1..15 = Song.instruments[inst - 1].
 *   fx / param: see MUSIC_FX_*; an effect persists on its channel until a row carries a note or
 *          another effect (a row with note 0 and fx 0 changes nothing).
 *
 * Timbre and modulation live in the Instrument (per-note, automatic) and in the cell effects (per-row):
 *   pulse timbre  = duty, or a 4-step duty sequence rotated every N frames (the RPG cry / PWM shimmer),
 *                   the NRx2 envelope (decay = pluck, step 0 = sustain, direction up = soft attack),
 *                   a pitch envelope (start N semitones up, fall onto the note: kicks, toms, plucks),
 *                   detune (a fixed period offset: two pulses a unit apart = chorus), auto-vibrato.
 *   wave timbre   = a 32-sample table, or a run of tables stepped every N frames (wavetable synthesis, LSDj
 *                   style: a PWM sweep, a bell that dulls), NR32 level steps as the only click-free dynamics
 *                   (decay full -> half -> quarter -> off = pluck/bell, or the reverse = swell).
 *   noise timbre  = NR43 clock + LFSR width (7-bit = tonal/metallic), NR42 decay, optional second stage.
 *
 * Panning (NR51, hard left / right / both per channel; mono on the handheld speaker): the driver owns NR51 through
 * a shadow byte = music_set_pan_base() mask (the game's, default 0xFF) & the music's own per-channel pans, written
 * only when the result changes (never per frame). Pans belong to the pulse lanes: MUSIC_FX_PAN on a note cell, the
 * pan pseudo-note on an effect-only cell, an echo cell with a side, or a pulse Instrument's `wave` byte (a fixed side
 * per note, or an auto-pan that alternates L/R every N frames). music_init() and music_stop() put every channel
 * back to both. A channel held by music_sfx() keeps whatever the SFX wrote in NR51 until the hold ends.
 */
#ifndef MUSIC_H
#define MUSIC_H

#include <stdint.h>

#define MUSIC_CH1 0x01   /* pulse 1: lead                          */
#define MUSIC_CH2 0x02   /* pulse 2: arpeggio chord or echo of ch1 */
#define MUSIC_CH3 0x04   /* wave: bass / drone                     */
#define MUSIC_CH4 0x08   /* noise: drums                           */

#define MUSIC_OFF 0xFE   /* note value: key off */
#define MUSIC_STACK_FRAMES 3        /* second drum of a cell stack */
#define MUSIC_DRUM_STAGE_FRAMES 2   /* a drum's own second stage (Drum.env2/poly2): the RPG kick = buzz, then hiss */

/* Effects (fx nibble). */
#define MUSIC_FX_NONE     0
#define MUSIC_FX_ARP      1  /* param = chord index: cycle note + Song.chords[4*param + i] every arp_speed frames (the fusion chord) */
#define MUSIC_FX_VIB      2  /* param = depth<<4 | rate: triangle vibrato, depth in period units, rate = frames per step */
#define MUSIC_FX_TRILL    3  /* param = frames<<4 | interval: alternate note / note+interval every frame for `frames` frames (0 = whole row); 2 = a mordent */
#define MUSIC_FX_SLIDE    4  /* param = signed period delta per frame (negative = pitch rises); persists until the next note */
#define MUSIC_FX_SPLIT    5  /* param = second MIDI note struck at the middle of the row (a 32nd-note pair) */
#define MUSIC_FX_VOL      6  /* param = 0..15 volume for this note (echo dynamics, accents, ghost notes) */
#define MUSIC_FX_CUT      7  /* param = frames after which the note is cut (staccato slap bass) */
#define MUSIC_FX_ECHO     8  /* ch2 only. param = delay<<4 | volume drop: ch2 replays ch1 `delay` frames late and quieter; 0 = off */
#define MUSIC_FX_ARPSPEED 9  /* param = new frames-per-arpeggio-step for the whole song */
#define MUSIC_FX_BEND    10  /* param = frames<<4 | signed 4-bit semitone offset: start `offset` semitones away and glide onto the written note in `frames` frames, then hold it (a bend that resolves) */
#define MUSIC_FX_TREM    11  /* param = depth<<4 | rate: tremolo, volume dips by `depth` steps every `rate` frames. Click-free on the wave channel (NR32 level), a re-strike on pulses: pads only, rate >= 6 */
#define MUSIC_FX_PORTA   12  /* param = frames: portamento, glide from the previous note's pitch onto this note in `frames` frames (1..255), then hold */
#define MUSIC_FX_PAN     13  /* pulse lanes. param = side (MUSIC_PAN_R / L / C): this note and the following ones sound on that side until the next pan; not a running effect (the channel's fx becomes none, as for a plain note) */

/* Pan sides: the two NR51 bits of a channel (bit 0 = right output, bit 1 = left output). */
#define MUSIC_PAN_R    1
#define MUSIC_PAN_L    2
#define MUSIC_PAN_C    3          /* both outputs: the default for every channel */
#define MUSIC_PAN_NOTE 0x80       /* pulse lanes: note byte 0x80 | side on an effect-only cell = a pan change (0x81..0x83; never 0xFE) */

typedef struct {
    uint8_t duty;  /* pulse: NRx1 duty bits (0x00 12.5%, 0x40 25%, 0x80 50%, 0xC0 75%); wave: unused */
    uint8_t env;   /* pulse: NRx2 (vvvv d sss: volume, direction 8 = up, step). wave: volume<<4 only
                      (0..15 maps to NR32: 1-4 quarter, 5-9 half, 10-15 full; the wave channel has no envelope) */
    uint8_t wave;  /* wave: index into Song.waves (16 bytes = 32 samples each). pulse: pan, bits 0-1 = side struck
                      with every note (0 = leave the channel's pan alone, 1 right, 2 left, 3 both), bits 2-7 = auto-pan
                      period in frames (0 = none): the held note alternates left / right every that many frames */
    uint8_t vib;   /* auto-vibrato on held notes: depth<<4 | delay in 4-frame units (0 = none) */
    uint8_t seq;   /* pulse: duty sequence, four 2-bit duties a<<6|b<<4|c<<2|d (0..3 = 12.5/25/50/75%) rotated every
                      `mod` rate frames without re-striking (the RPG duty-cycle pattern). wave: number of extra tables
                      after `wave` (waves wave..wave+seq) stepped every rate frames from the note start; each step
                      rewrites wave RAM behind NR30 = 0 and re-triggers (a small click; rate >= 2) */
    uint8_t mod;   /* bits 0-2: sequence rate in frames (0 = no sequence, static duty / single table)
                      bit 3: wave sequence loops (0 = hold the last table: a one-shot attack)
                      bits 4-7: detune, signed period units -8..7 added to every pitch (chorus pairs, octave fatness) */
    uint8_t penv;  /* pitch envelope on every note: semitones<<4 | frames. Start `semitones` (1..15) above the written
                      note and glide down onto it in `frames` (1..15), then hold: 12/5 = a pulse kick, 12/1 = a pluck
                      (hUGETracker's "start an octave up"), 5/3 = a tom. 0 = none */
    uint8_t wenv;  /* wave only. NR32 level steps every (wenv & 0x7F) frames; 0 = none. bit 7 = 0: decay
                      full -> half -> quarter -> off (pluck / bell; the note ends by itself), bit 7 = 1: swell
                      quarter -> half -> full and hold (a pad fade-in). Click-free: NR32 needs no re-trigger */
} Instrument;

typedef struct {
    uint8_t env;   /* NR42 */
    uint8_t poly;  /* NR43: clock shift<<4 | LFSR width (8 = 7-bit, tonal) | divisor */
    uint8_t env2;  /* optional second stage struck MUSIC_DRUM_STAGE_FRAMES later (0 = none): NR42 */
    uint8_t poly2; /* second stage NR43 */
} Drum;

typedef struct {
    uint8_t frames_per_row;    /* tempo: 9 = 100 bpm at 16th-note rows (3600 / bpm / 4) */
    uint8_t rows_per_pattern;  /* 16 = one 4/4 bar of 16ths */
    uint8_t arp_speed;         /* frames per arpeggio step (3..4 is the fusion rate) */
    uint8_t n_orders;          /* song length in patterns (bars) */
    uint8_t loop_to;           /* order index the song restarts from */
    const uint8_t *orders[4];           /* per channel: n_orders pattern ids */
    const uint8_t *const *patterns;     /* pattern id -> rows_per_pattern * 3 bytes */
    const Instrument *instruments;
    const uint8_t *chords;              /* 4 semitone offsets per chord, 0xFF = unused slot */
    const uint8_t *waves;               /* 16 bytes per wave shape */
    const Drum *drums;
} Song;

void music_init(const Song *song);          /* start a song from its first row (NULL = silence) */
void music_tick(void);                      /* once per frame after wait_vbl_done(); no-op without a song */
void music_stop(void);                      /* silence the four channels and forget the song */
void music_set_volume(uint8_t vol);         /* master music volume 0..15 (default 15); scales every channel */
uint8_t music_playing(void);                /* 1 while a song is loaded */
uint8_t music_bar(void);                    /* current order (bar) index: handy for picture-follows-music effects */
uint8_t music_row(void);                    /* current row inside the bar (0..rows_per_pattern-1) */

/* SFX contract: an effect that writes a channel's registers calls this first with the channel bits it
 * uses and roughly how many frames it lasts. The driver leaves those channels alone and re-strikes
 * their notes when the hold runs out. */
void music_sfx(uint8_t channels, uint8_t frames);

/* Panning base: the game's NR51 mask (default 0xFF, every channel to both outputs). The driver ANDs its own pans
 * into it and writes NR51 only when the result changes, so the game never writes NR51 itself: call this once at
 * boot after NR52 / NR50 (it writes NR51 at once), and again when the game wants a channel on one side. */
void music_set_pan_base(uint8_t mask);

#endif
