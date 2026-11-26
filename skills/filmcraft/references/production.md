# Local production tools

Use any editor for final production. The included local assembler handles a straight-cut sequence of stills or finished video shots, one sound source per scene, and an optional bottom-half presenter. Design custom animation as source clips. Mix narration, music and effects to a prepared track before assembly when a scene needs several stems. The booklet generator demonstrates one way to animate original graphics.

## Commands

From the repository root, set your working directory to it and run:

```sh
python skills/filmcraft/scripts/film.py check skills/filmcraft/examples/booklet/film.json
python skills/filmcraft/scripts/film.py script skills/filmcraft/examples/booklet/film.json
python skills/filmcraft/examples/booklet/make_booklet.py productions/booklet
python skills/filmcraft/scripts/film.py render productions/booklet/film.json productions/booklet.mp4
```

Python 3.10+ is sufficient for check and script. Render needs an FFmpeg build with H.264 (libx264), AAC and standard video filters; drawtext is needed when a status label is specified. Only the **demo generator** needs Pillow 10.1+ (`python -m pip install "Pillow>=10.1"`). Both media commands accept `--ffmpeg PATH`. A failed or existing output never replaces a completed export. Keep production inputs you own outside the public skill.

## Manifest

Start from [the actual JSON example](../examples/booklet/film.json). Top-level fields are title, integer fps, even [width,height], sources mapping, and ordered scenes. Duration is the sum of scene frames. `check` validates structure, durations and evidence references. It does not open sources or evaluate prose. `script` prints only spoken lines; it has no model/API dependency. `render` resolves media paths relative to the manifest and fully decodes the assembled output before delivery.

| Scene field | Meaning |
| --- | --- |
| id, seconds | Unique ID; positive duration on an exact frame boundary (e.g. 2.5s at 24 fps). |
| basis, evidence | Use documented, observation, proposal, fiction or transition. For the first three, include an array of source IDs declared in sources. |
| voice, picture, change, sound | Recording-ready line (empty for silence); framing/action at entry and exit; viewer or physical change; sound cue. |
| file, in | Local still/video for this shot and optional source start in seconds. Stills hold. Videos must cover the interval. |
| audio, audio_in | Ready-mixed local audio plus optional start in seconds; omit audio for silence. Use @picture or @presenter for original clip audio with automatic sync. Narration text is never synthesized implicitly. |
| presenter, presenter_in | Optional local video. The picture fits in the top half, performer fits in the bottom half. Both retain their aspect ratio. For other framing, supply a precomposed shot instead. |
| screen_label, spoken_qualification | For a proposal, give a short visible status label and, when voiced, the exact qualifying phrase included in voice. The label is burned in. A person still checks whether the qualification is meaningful and readable. |

For a ready sync shot: set `file` to your screen capture, `presenter` to the actor’s recorded MP4, `audio` to `@presenter` and `presenter_in` to the source start. For a single longer voice master, reference the same audio file and advance `audio_in` to each scene’s measured boundary. Pad an intentional short stem with room tone in the sound edit. For source clips containing multiple streams, prepare/select the intended stream first; the assembler uses the first video and first audio stream.

## Final handoff

Include the MP4, clean narration, separate caption file aligned to the actual performance when speech is present, asset/source credits and editable plan. Caption groups follow actual phrase boundaries; include speaker identity or relevant sound when it is needed to understand the action. Keep alternate social endings separate. Open the final file, seek across cuts, check the last syllable and ensure the intended MP4 is actually accessible from the delivery location. For a silent-led film, inspect its on-screen language and meaningful sound cues.
