# Presentation script: gbc-music in 5-10 minutes

Audience: technically literate, has never seen a Game Boy sound register. Goal: in under ten minutes they hear a
song the system wrote, understand why it sounds like a cartridge, see the three outputs, and see that every claim
is checked by a machine and a human.

## Before the room (10 minutes, the day before)

1. Pre-render the fallback set in `demo/` with the commands of "Live commands" below (keep the directory): `main.txt`,
   `main.gbc`, `main.mid`, `main.wav`, `main.mp3`, `probe/pianoroll.png`, `probe/audio_report.json`, a player screenshot.
2. Open the demo page (audio clips, the interactive piano roll, the probe picture) in a
   browser tab and play ten seconds of each clip once (caches the audio). One song at a time: the page pauses the
   others.
3. Have a terminal open in `demo/` with `SKILL` exported and the python on PATH; run `python $SKILL/scripts/compose.py
   styles` once to warm the disk.
4. Headphones or a speaker connected and tested with the MP3. A Game Boy with a flash cart and `main.gbc` on it if
   you have one (the ROM plays on hardware; show it, do not depend on it).

## The script

| time | what you do | what you say |
|---|---|---|
| 0:00 | Play `main.mp3` for 20 s (the demo page or the file). | "That is a Game Boy Color playing a song a program wrote this morning from one line: fusion style, F sharp, 100 bpm, 32 bars, seed 7. Nothing was hand-placed. Hold that sound in your head." |
| 0:30 | Slide / page: the four channels (two pulses, wave, noise). | "The problem: the chip has four voices and almost no knobs. Two square waves with four duty cycles, one 32-sample wave you can draw, and a noise generator. Volume on the squares only changes when you re-strike the note. That is the whole palette. Most generated chip music sounds like a toy because it ignores what those constraints make good." |
| 1:30 | Page: DESIGN_NOTES table (three rows: duty is free, volume re-strikes, wave level is click-free). | "So we measured instead of guessed. We logged every register write of four commercial cartridges, transcribed two classic soundtracks bar by bar, and listened. Three facts drive the design: changing the pulse's duty is free, changing its volume clicks, and the wave channel is the only voice with smooth dynamics. The cartridges switch instruments between phrases, not between notes; when they do switch note to note they change the envelope and keep the duty; their vibrato is late and shallow; their bends are rare and always land." |
| 3:00 | Terminal: `compose.py generate ... --seed 8` (a different seed) then `song_wav.py` and play 15 s. | "The generator is deterministic: same arguments, same song, every time, so a game's soundtrack is reproducible and reviewable. Form, harmony, texture and an 'organic' layer are separate knobs: a stage loop with fusion idioms is one flag, not a contradiction. Seed 8 is a different tune with the same rules." |
| 4:30 | Terminal: open `main.txt`, point at one bar. | "The output is text a human can edit: four lanes, sixteen cells per bar, one effect per cell. `:maj7` is a chord cycled at frame rate on one voice, which is how you get a chord out of a square wave. `/-2,6` is a bend from a tone below that lands in six frames: the rule: bends must resolve." |
| 5:30 | Page: the interactive piano roll with the playhead; then the player screenshot; then the MIDI in a DAW or just the file. | "Three outputs from the same score. The ROM runs on the real hardware and in any emulator; here it is in the player with a live bar counter. The MIDI puts it in a DAW: one track per voice, chords expanded, bends as pitch bend. The WAV is the chip itself, rendered headlessly in a cycle-exact emulator, not an approximation." |
| 7:00 | Page: `pianoroll.png` and the probe numbers (four channels, pitch changes, arpeggio detected). | "And nothing ships on trust. A probe runs the ROM five times, once per isolated channel, and reports what actually sounds: four channels active, three hundred pitch changes in ten seconds, the chord cycle at three frames per step. In the pipeline this was built in, an automated judge runs the same probe on every build, and a human listens to the pages, one song at a time, and says what is wrong. Those verdicts became rules in the skill." |
| 8:30 | Close. | "So: a complete music system for a 1998 sound chip, measured not guessed, deterministic, three outputs, verified by machine and by ear, and written so an autonomous coding agent can use it from a one-line brief. Questions." |

Talking points in reserve: why no hardware sweep (it runs across notes and fights re-triggers); why the wave
channel plays an octave down (same period, half the frequency: the driver adds the octave); why 75% duty equals 25%
on a mono speaker; the SFX hand-over (`music_sfx`: the effect borrows a channel, the driver re-strikes the note after);
what the organic layer measured (bar-rhythm reuse 0.9 vs 0.44, rests 0.03 vs 0.24).

## Live commands (copy-paste; each prints a JSON line)

```
export SKILL=/path/to/skills/gbc-music
mkdir demo && cd demo
python $SKILL/scripts/compose.py generate --style fusion --key F# --bpm 100 --bars 32 --seed 7 --organic 2 --out main.txt --report gen.json
python $SKILL/scripts/song_rom.py main.txt --out main.gbc
python $SKILL/scripts/song_midi.py main.txt --out main.mid --report midi.json
python $SKILL/scripts/song_wav.py main.txt --out main.wav --mp3
python $SKILL/scripts/audio_probe.py --rom main.gbc --out probe --pre wait:60 --seconds 10
python $SKILL/scripts/compose.py generate --style fusion --key F# --bpm 100 --bars 32 --seed 8 --organic 2 --out seed8.txt
python $SKILL/scripts/song_wav.py seed8.txt --out seed8.wav --seconds 20 --mp3
```
Wall clock on the author's laptop: generate < 1 s, ROM build 2-3 s, MIDI < 1 s, WAV of 77 s about 4 s, probe about 25 s
(five emulator passes). Run the probe before the room or while talking.

## Fallback if the toolchain misbehaves

- **GBDK / make fails**: skip the ROM and WAV steps live; play `demo/main.mp3` (pre-rendered) and show
  `demo/main.gbc` in the published player page (it runs in the browser). Say so plainly: "the build toolchain is
  being difficult; this is yesterday's render of the same command".
- **PyBoy fails** (WAV, probe): same; `probe/audio_report.json` and `pianoroll.png` are pre-rendered.
- **No audio output**: the published page has the clips; a phone can open the private link.
- **Everything fails**: the published demo page alone carries the whole script (clips, roll, probe picture, the score
  text, the three downloads). Walk it top to bottom; the timings above still hold.
- **A question you cannot answer**: `docs/LIMITS.md` and `docs/DESIGN_NOTES.md` are on the page's links; say "it is
  in the limits document" and move on.
