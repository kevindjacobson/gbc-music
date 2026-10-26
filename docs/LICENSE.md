# Licence

This skill (everything under `skills/gbc-music/`: the driver, the compiler and generator, the three outputs, the
probe, the player template, the piano-roll runtime and these documents) is released under the **MIT License**,
copyright 2026 Kevin Jacobson. The licence text is in `LICENSE` at the skill root.

## Provenance of the measured facts

The design rules, wave tables, drum register pairs and corpus statistics in `DESIGN_NOTES.md` were measured by the
author from cartridges the author owns (register traffic logged in an emulator) and from the author's own
transcription and disassembly research. No audio, code or data was copied from any of those works: the wave
tables are 16-byte register images and the drums are two-byte register pairs, recorded as facts about what the
hardware was told to do; the progressions are Roman-numeral patterns; the corpus numbers are counts.

External tools used by the scripts (GBDK-2020, PyBoy, numpy, Pillow, lame, ffmpeg, mido for the round-trip test)
are not bundled and carry their own licences.
