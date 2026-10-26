# Piano roll component (animated, zoomable, playhead synced to its clip)

`pianoroll.js` is one inline script for listening pages (single-file HTML). Canvas based, no
external loads, colours as CSS tokens, DPR aware, redraws only on requestAnimationFrame while its clip plays or
the user interacts, so a page with six rolls stays cheap. Each roll animates only while the audio it is bound
to is playing (or while its clock moves). `prefers-reduced-motion` drops the glow on sounding notes, not the playhead.

Files here: `pianoroll.js` (the component), `events/*.json` (events for the published pages), `headless/`
(verification screenshots + result JSONs from headless Chrome under a strict CSP).

## Data: `compose.py events`

```
python scripts/compose.py events <score.txt>... --out events.json [--offset <seconds>] [--fps 59.7275]
```

Replays the compiled patterns exactly as `src/music.c` reads them (same compiler, same bytes) and writes one
JSON object:

| key | meaning |
|---|---|
| `fps`, `frames_per_row`, `rows_per_bar`, `bars`, `loop_bar`, `arp_speed`, `bpm` | tempo info for bar lines, beat ticks and the loop marker (`loop_bar` 0-based) |
| `seconds_per_bar`, `length_s` | derived; `length_s` = one pass of the song |
| `offset_s` | the `--offset` you passed (added to every `t`); the component has its own `offset` option too |
| `channels` | `["pulse 1", "pulse 2", "wave", "noise"]` |
| `songs` | `[{name, title, source, start_bar, bars, loop_bar, start_s, notes}]`; several scores on the command line are chained back to back (the timbre demo chains three) and bar numbers continue |
| `instruments` | the `inst` lines as dicts (`name`, `type`, `duty`, `env`, ...) |
| `notes` | the events, sorted by frame |

One note:

```
{"ch": 0..3, "t": seconds, "d": seconds, "f": frame, "fd": frames, "bar": 0-based, "row": 0-based,
 "midi": 36..107 (noise: a pseudo pitch from NR43 so kicks sit low and hats high), "vol": 0..15, "inst": name,
 optional: "drum": "K" (noise), "dec": seconds until the envelope reaches silence (pulse/noise NRx2 decay, wave
 NR32 steps), "arp": [intervals] + "arp_f": frames per step (the chord cycle, NOT expanded: the roll draws the
 cycle itself when zoomed in and a translucent band when zoomed out), "trill": iv, "mordent": iv, "split": true
 (the second note of a 32nd pair), "bend": [semitones, frames], "porta": frames + "porta_from": previous midi,
 "slide": period units per frame, "vib": [depth, rate], "autovib": [depth, delay frames], "trem": [depth, rate],
 "penv": [semitones, frames], "cut": frames, "echo": true (a pulse-2 copy of a pulse-1 note made by FX_ECHO:
 delayed by the echo's frames, quieter by its drop)}
```

`t = offset + f / fps`, `d = fd / fps`. `d` is the gate: until the lane's next note, key-off or cut. A note whose
envelope dies earlier carries `dec`; the roll draws the solid part for `min(d, dec)` and the rest faded.

## Aligning to a clip

The roll needs the second at which music frame 0 (the `music_init` tick) sounds inside the audio it is bound to.
Measured for the published pages (first audible onset in the file, the row-0 strike):

| page | clip | offset | how |
|---|---|---|---|
| song-form | `full_<song>.mp3` (headless PyBoy render) | stage 0.7101, blend 0.7111, pop 0.7113, rock 0.7111, blues 0.7111, the AABA fusion song 0.7115 | the render trims to 0.1 s before the first non-silent sample, which is PyBoy's boot chime (frame 35); the music starts at frame 73 (0.711 s into the file). Chrome decodes the MP3 to within 0.14 ms of the WAV. |
| timbre | `demo_mono8.wav` (capture from the frame the wave channel came on) | 0.0009 | first non-silent sample of the file |
| duet | lockstep WasmBoy cores | 0.1144 s of core time (frame 6, sample 616 of 739) | measured with the raw core in node; PyBoy numbers do not apply (PyBoy plays its boot chime first) |

## API

```js
const roll = GbcPianoRoll.create(containerEl, eventsJson, {
  audio: audioEl,        // bind to an <audio>; playhead = audio.currentTime - offset
  offset: 0.7101,        // seconds into the audio where music frame 0 sounds (default eventsJson.offset_s)
  range: [34.3, 36.4],   // optional: the clip is this slice of a longer recording (range players); roll shows it
  clock: () => seconds,  // instead of audio: a clock-bound roll (duet cores); music seconds or null; no seeking
  height: 240, follow: true, seek: true, title: 'text', sections: [{label, start_bar, bars}]
});
roll.bind(audio, {offset, range}); roll.bindClock(fn); roll.setRange([s, e] | null); roll.fit(); roll.fitAll();
roll.zoom(factor[, anchorSec]); roll.pan(seconds); roll.setFollow(bool); roll.seek(musicSec); roll.time();
roll.state(); roll.redraw(); roll.destroy(); roll.playheadX; roll.canvas; roll.audio
```

Declarative: `GbcPianoRoll.mountAll()` mounts every `<figure data-pianoroll data-events="#jsonScriptId"
data-audio="#audioId" data-offset="0.7101" [data-range="s,e"] [data-title=".."] [data-height="240"]
[data-sections="#jsonId"]>` and sets `figure.__roll`. A static fallback (`<img class="pr-fallback">` or any `<img>`
inside the figure, e.g. the probe PNG) is hidden once the live roll exists, so the page degrades to the PNG
without script.

Controls: zoom in / out buttons, `+` `-` keys, wheel (ctrl/meta or pinch anywhere; plain wheel once the roll has
focus), two-finger pinch; pan by drag, shift-wheel, horizontal wheel, arrow keys; `fit` (the clip) and `all` (the
whole song when a range is set), `0` key, double click; `follow` toggle (`f`) keeps the playhead in view while
playing; click seeks the audio (not for clock-bound rolls). Hover shows bar.row, seconds and the note under the
pointer with its effects in the toolbar. Sounding notes light up. The loop bar is a dashed red line; playback past
one pass wraps the playhead to the loop bar.

Colour tokens (set them on the container or `:root`, with dark-mode blocks): `--pr-pulse1 --pr-pulse2 --pr-wave
--pr-noise --pr-bg --pr-grid --pr-grid-strong --pr-ink --pr-muted --pr-playhead --pr-lit --pr-key --pr-panel --pr-line`.

## Minimal usage (10 lines)

```html
<audio id="a1" controls preload="metadata" src="data:audio/mpeg;base64,..."></audio>
<figure data-pianoroll data-events="#ev1" data-audio="#a1" data-offset="0.7101" data-title="stage">
  <img class="pr-fallback" alt="piano roll" src="data:image/png;base64,..."></figure>
<script type="application/json" id="ev1">{ ...compose.py events output... }</script>
<script>/* inline pianoroll.js here */</script>
<script>
  var rolls = GbcPianoRoll.mountAll();          // or GbcPianoRoll.create(fig, json, {audio: a, offset: 0.71})
  // range player: rolls[0].setRange([34.289, 36.432]); a.currentTime = 34.289; a.play();
  // clock-bound: GbcPianoRoll.create(fig, json, {clock: function () { return frames / 59.7275 - 0.1144; }});
</script>
```

Keep the page's exclusive-audio snippet: the roll never starts audio by itself.
