# Architecture

```
 idea / brief                                  the score (text)                         ROM tables (C)
 ──────────►  compose.py generate  ──────────►  main.txt  ──────────►  compose.py compile  ──────────►  music_data.c|h
               style, key, bpm, bars, seed        │  (edit by hand)                                     │
               form → progression → texture       │                                                     ▼
               → organic → timbre plan            ├──► song_midi.py  ──► main.mid           music.c + a game  ──► game.gbc
                                                  ├──► song_rom.py   ──► player.gbc ──┐     music.c + player ──► player.gbc
                                                  └──► song_wav.py   ──► main.wav/mp3 │                              │
                                                       (song_rom + PyBoy)             └──────► audio_probe.py ◄──────┘
                                                                                                  audio_report.json, audio.wav,
                                                                                                  pianoroll.png
                                                  compose.py events ──► events.json ──► pianoroll.js (interactive roll on a page)
```

## 1. The driver (`scripts/music.c`, `music.h`)

A tracker: a song is ROM tables (`Song` in `music.h`), one **order list per channel** of pattern ids, each
**pattern** one bar of `rows_per_pattern` rows, each **row** a 3-byte cell `[note][inst<<4 | fx][param]`. Tempo is
`frames_per_row` (a row is a sixteenth note; 9 frames at 100 bpm). `music_tick()` runs once per frame right after
`wait_vbl_done()`: it reads the row on a row boundary, then updates the three tonal channels (pitch this frame from
the effect state, timbre motion from the instrument) and the noise channel (drum stacks and second stages).

Per-channel state is small (one `Chan` struct per voice: note, instrument, volume, effect, arpeggio slot and timer,
vibrato phase, frames held, SFX hold, cut, glide remaining / current / step, slide, period). The driver never
touches the master registers NR50/NR51/NR52 (the game's `sfx_init()` owns them) and never uses the hardware sweep
NR10 (pulse 1 only, runs across notes, fights re-triggers): every pitch movement is software on NRx3/NRx4, so
pulse 1, pulse 2 and wave behave identically.

Register facts the driver is built on (Pan Docs, confirmed in emulation): NRx3/NRx4 written without the trigger
bit change pitch without re-striking (arpeggios, vibrato, glides are click-free); NRx1 duty bits can be rewritten
any frame (duty sequences are free); NRx2 only loads on a trigger (every pulse volume change is a re-strike);
NR32 (wave level full / half / quarter / off) changes silently (the wave channel's click-free dynamics); wave RAM
can only be rewritten with NR30 = 0 and the channel must then be re-triggered (a wavetable step costs a small click).
The wave channel plays a period an octave below the pulse table, so the driver looks up `period(note + 12)` for it.

**Instrument** (8 bytes): duty, NRx2 envelope (wave: volume), wave index, auto-vibrato (depth, delay), `seq` (4 x 2-bit
duty sequence, or the number of extra wave tables), `mod` (sequence rate | wave loop bit | signed detune), `penv`
(pitch envelope: semitones, frames), `wenv` (NR32 level steps: frames per step, bit 7 = swell).
**Drum** (4 bytes): NR42, NR43, optional second stage NR42/NR43 struck 2 frames later.
**Effects** (fx nibble): arpeggio, vibrato, trill/mordent, raw slide, 32nd split, volume, cut, echo (pulse 2 replays
pulse 1 from a 16-frame ring buffer), arpeggio speed, resolving bend, tremolo, portamento. One effect per cell; an
effect persists on its channel until a row carries a note or another effect.

**SFX contract**: `music_sfx(channels, frames)` makes the driver stop writing those channels for that long and
re-strike their notes afterwards. A game's effects call it before touching registers (`INTEGRATION.md`).

Cost: a few hundred cycles on a quiet frame, about 1.5-3k when all four channels move; the wave-table step
(16-byte copy behind NR30 = 0) is the one expensive event.

## 2. The score format and the compiler (`compose.py compile`)

The score is text (`SCORE_FORMAT.md`): a header (`name:`, `title:`, `bpm:` or `tempo:`, `rows:`, `arp:`, `loop:`),
`inst` / `wave` / `chord` / `drum` library lines, then `bar N` blocks with up to four lanes (`lead:` pulse 1,
`arp:` pulse 2, `bass:` wave, `drum:` noise) of 16 cells. `parse_score()` builds a `Song` (instruments, the built-in
plus custom waves, chords and drums, bars -> lanes -> cells); `compile_song()` turns every cell into its 3 bytes
(`compile_cell`), interns identical bar lanes as one pattern (a repeated bar costs one byte per channel), collects
the chord, wave and drum tables; `emit_c()` writes `music_data.c` (the tables) and `music_data.h`
(`extern const Song <name>;`) and a report per song: bars, frames per row, bpm, unique patterns, instruments, chords,
waves, drums, notes, effects used, ROM bytes, warnings (out-of-range notes are clamped and reported; tremolo on a
pulse under 6 frames and wave sequences at rate 1 warn about clicks). Several scores compile into one file.

Sizes: 12 bars of unique material are about 2 KB; a 32-bar fusion theme 5-6 KB; an ambient bed under 1 KB. All of it
sits in bank 0 next to the game's code.

## 3. The generator pipeline (`compose.py generate`)

Deterministic: the same arguments always give the same score (two random streams, one for the tune and one for
the bend decisions, so `--bend` never changes the notes). The stages, in order:

1. **Style** (`--style fusion|ambient|chip|pop|rock`): picks the instrument set, the register ranges, the kit and the
   default form. `fusion`, `ambient` and `chip` have their own loop generators (`--form loop`); `pop` and `rock` always
   go through the form engine; `fusion` can also take `aaba` and `verse-chorus`.
2. **Form** (`--form auto|loop|stage|verse-chorus|aaba|blues12`): `build_plan()` lays out sections with roles and bar
   counts from `--bars` (stage 16 / 24 / 28: (intro 4) A 8 B 8 C 8; verse-chorus 32 / 48 / 64; aaba 32 / 40;
   blues12 28 / 40 / 52) and sets `loop:` past the intro.
3. **Progression** (`--progression <name>|"I V vi IV"|"stage_a | stage_b | stage_c"`): Roman numerals resolved against
   `--key`; the verse takes the rotation that starts off the tonic so the chorus's I is an arrival; the pre-chorus
   ends on V; the bridge starts on a chord the song has not used; stage sections each get their own progression.
   The mode (major / mixolydian / minor) is read off the numerals and picks the lead's scale.
4. **Texture** (`--texture plain|fusion`): independent of the form. `plain` = triads / power chords, a straight kit,
   vibrato on held notes; `fusion` = colour tones on the pulse-2 cycle (maj -> maj7, min -> m9, power chord -> add9),
   a mordent opening each phrase and a trill on its target, slap bass with octave pops, the 16th-note fusion kit,
   and the echo voice in the bridge / B section.
5. **Lift** (`--lift fifth|sixth|octave`, default fifth): how far the chorus, the C section, the final A or the
   second blues head sits above the verse. Applied at generation (it sets that section's lead centre); the RPG
   corpus's second-section lifts span 1-8 semitones, so a fifth is the default and the octave the maximum.
6. **Organic layer** (`--organic 0|1|2|3`, `apply_organic()`): a seeded, deterministic post-pass on the finished
   score. 1 = repeats on phrase ends vary, phrase-end breaths, a fill closes every section, off-beat `v` accents, a
   lead colour per section, a second bass table in B sections; 2 = + half of all repeats vary (an inner note too),
   mid-phrase breaths, dropped hats, pulse 2 sits out one bar in 16, bass anticipations as plucks, lead stab pairs on
   repeated notes, bass table alternation on octave bounces, the RPG kit in B sections (plain texture); 3 = + density
   ebbs in bars 3 and 7 of a section. Harmony, tempo, form, bends and `loop:` are untouched; the moves are counted in
   the report (`organic_moves`) and named in the score's header comment.
7. **Timbre plan** (`apply_timbre_plan()`, part of `--organic`): the instruments the organic levels switch to,
   following the measured cartridge habits in `DESIGN_NOTES.md`. It emits `inst` lines only when used (15 per song
   cap) with fixed names: `lead_round` (`pulse duty=50 env=C7 vib=2:3`), `lead_bright` (`duty=25`), `lead_shimmer`
   (`duty=50,25 rate=2`), `lead_stab` (`duty=50 env=F3`), `bass_b` (`wave vol=12 shape=organ2`), `bass_pluck`
   (`wave vol=15 shape=tri decay=4 penv=12,1`), `bass_alt` (`wave vol=12 shape=pwm50`; the fusion texture reuses its
   own triangle bass instead). Switches land on a section's first note; an articulation pair tags the short note
   `@lead_stab` and the next note re-tags the section lead; never detune. The section plan comes from the form
   generators (`Score.sections`: role, start, bars); the legacy loops fall back to 8-bar blocks. Counts:
   `lead_timbre_by_section`, `lead_stab_pair`, `bass_table_alternation_bars`, `bass_pluck_anticipation`.

The generated score is compiled once as a self-check before it is written, and the report carries the plan
(`form`, `texture`, `lift`, `progression`, `numerals`, `chords`, `progressions`, `mode`, `loop_bar`, `plan` with one
entry per section: `section`, `role`, `start_bar`, `bars`, `numerals`, `chords`; `organic` and `organic_moves` when
set) next to the compile report.

`compose.py split` writes one score per part (lanes kept, the rest silenced, header shared) for multi-ROM pieces
played in lockstep. `compose.py events <score>... --out events.json [--offset s] [--fps 59.7275]` writes every note
for the interactive piano roll: the file carries `fps`, `frames_per_row`, `rows_per_bar`, `bpm`, `bars`, `loop_bar`,
`arp_speed`, `offset_s`, `seconds_per_bar`, `length_s`, `channels`, `songs` (several scores chain back to back and
must share tempo and rows), `instruments`, and `notes`, one object per note: `ch` 0..3, `t` seconds (offset + frame /
fps), `d` gate seconds (to the lane's next note, key-off or cut), `f` / `fd` frame and frames, `bar`, `row`, `midi`
(noise: a pseudo pitch from NR43), `vol`, `inst`, plus the effect it carries (`drum`, `dec` envelope lifetime, `arp`
intervals + `arp_f`, `trill` / `mordent`, `split`, `bend`, `porta` + `porta_from`, `slide`, `vib`, `autovib`, `trem`,
`penv`, `cut`, `echo`). Chord cycles are flagged, not expanded (the MIDI export expands them).

## 4. The listener (`audio_probe.py`)

Headless PyBoy with sound emulation, deterministic. Five passes over the ROM with identical input: one normal
stereo mix (the WAV), and one per channel with NR51 forced to that channel alone after every frame, so each voice is
analysed on its own. Two windows: `title` after `--pre` (default `wait:150`) and `play` after `--script` (default
`press:start;wait:60`). Per channel: RMS activity per frame, autocorrelation pitch per frame rounded to MIDI,
pitch changes, onsets, arpeggio runs (>= 6 pitch changes spaced 2-6 frames apart through >= 3 notes), drum hits on
noise. `music_detected` = at least two channels active over 15% of the window and at least 8 pitch changes on the
tonal channels. Outputs: `audio_report.json`, `audio.wav` (the play window), `pianoroll.png` (pitch per channel over
time, noise as hits). `solo_reliable: false` means the game rewrites NR51 every frame and the per-channel numbers
are approximate.

## 5. Listening pages

Every claim about sound is shown, not described: the pages built while developing this (engine proof, song form, timbre,
duet, organic comparison, the interactive piano roll) are single-file HTML pages that carry the
generated audio, the probe pictures and the scores side by side. Rules that apply to any page built from this
skill: one song at a time (an exclusive-audio snippet pauses every other `<audio>` when one plays), external
scripts only from pinned CDN versions, phone-width friendly. `pianoroll.js` (plain ES5, no dependencies, one global
`GbcPianoRoll`, colours from CSS custom properties `--pr-pulse1` ... `--pr-line` with fallbacks) renders the
events JSON as an animated, zoomable roll with a playhead bound to an `<audio>` element. A page inlines the file and
declares a figure:

```html
<audio id="a1" controls preload="metadata" src="data:audio/mpeg;base64,..."></audio>
<figure data-pianoroll data-events="#ev1" data-audio="#a1" data-offset="0.711" data-title="main"
        data-range="s,e" data-sections="#planJsonId" data-height="240">
  <img class="pr-fallback" src="data:image/png;base64,..." alt="piano roll"></figure>
<script type="application/json" id="ev1">{ ...compose.py events output... }</script>
<script>/* contents of pianoroll.js */</script>
<script>GbcPianoRoll.mountAll();</script>
```
or `GbcPianoRoll.create(el, eventsJson, {audio, offset, range, clock, height, follow, seek, title, sections})`
with `bind`, `bindClock`, `setRange`, `fit`, `fitAll`, `zoom`, `pan`, `setFollow`, `seek`, `time`, `state`, `redraw`,
`destroy`. `offset` is the second of the clip at which music frame 0 sounds (0.710-0.712 for a game ROM rendered
from boot: the boot chime comes first and the song starts at frame 73; 0 for `song_wav.py` output, which cuts the
chime and starts on the song's first sounding sample). The `<img>` is the no-script fallback and is hidden once the roll mounts. `docs/PIANOROLL.md` is
the runtime's own README (data format, API, measured clip offsets).
