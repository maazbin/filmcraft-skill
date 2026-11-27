# Filmcraft

**Filmcraft is now part of [Creator Runbook](https://github.com/maazbin/creator-runbook).** Install Creator Runbook for new productions. It includes the standalone writing prompt, documentary exercises and original booklet animation. Existing Filmcraft projects can use their current `film.json` and media folders. [Open an existing project in Creator Runbook](https://github.com/maazbin/creator-runbook/blob/main/skills/creator-runbook/references/filmcraft-plans.md).

Write the words a performer can say and the shots an editor can actually make. Filmcraft is a model-independent skill for short films, longer documentaries, animated stories and explainers. It works as a plain prompt, an installable agent skill, or a local Python/FFmpeg production workflow.

**Try the [21-second animated booklet film](media/booklet-study.mp4)** · **Read [a complete five-minute documentary script](skills/filmcraft/examples/documentary/the-corner.md)**

## Start with your model

- **Chat only:** paste [START-HERE.txt](START-HERE.txt) into any chat, fill in the brief at the bottom, and attach the sources you want it to use. For long work, carry the continuity record from chapter to chapter.
- **Agent with file access:** clone this repository, open it and ask the agent to follow [SKILL.md](skills/filmcraft/SKILL.md). Install by copying the entire `skills/filmcraft` folder into the skill directory your host uses, such as `~/.codex/skills/` or `~/.claude/skills/`. No account or model API key is needed to use the prompt, examples or local tools.
- **Editor:** start from the [film plan](skills/filmcraft/examples/booklet/film.json), run the [local tools](skills/filmcraft/references/production.md), or use the timed script in your preferred NLE.

> Use Filmcraft to write a five-minute archival film about the two versions of Migrant Mother. Write for a viewer who recognizes the portrait. Use the Library of Congress series guide and the two original object records. Give me recording copy and a timed edit. Preserve any uncertainty about why the photograph was changed.

## What comes back

A recording-ready script, an audio/visual paper edit, and a ledger of sources, limits and missing material. For longer films, a chapter budget and continuity record keep time and evidence consistent. For production, use your own recording, approved TTS, a presenter clip or a caption-led sequence. HeyGen is optional. No paid calls or uploads happen in the included programs.

| If the draft feels weak | Open |
| --- | --- |
| The voice sounds generic or written for a page | [Three line repairs and a table read](skills/filmcraft/references/script-desk.md) |
| The middle of a longer film repeats itself | [Formats and chapter construction](skills/filmcraft/references/formats.md) |
| The interview only supports part of the story | [A documentary paper edit with missing evidence](skills/filmcraft/references/documentary-example.md) |
| A shot says “cinematic” but gives the editor no action | [Staging, motion, sound and review](skills/filmcraft/references/direction.md) |
| The voice is slow or the avatar is out of sync | [Optional voice and presenter workflow](skills/filmcraft/references/voice.md) |
| Each platform needs its own copy | [Publishing for six platforms](skills/filmcraft/references/posting.md) |

## Run the example

Requirements: Python 3.10+, Pillow 10.1+ for the demo art, and FFmpeg with libx264 and AAC for media. Use an empty production directory. The first command below needs only Python’s standard library.

```sh
python skills/filmcraft/scripts/film.py check skills/filmcraft/examples/booklet/film.json
python -m pip install "Pillow>=10.1"
python skills/filmcraft/examples/booklet/make_booklet.py productions/booklet
python skills/filmcraft/scripts/film.py render productions/booklet/film.json productions/booklet.mp4
```

The sample is a caption-led animation with original synthesized paper sounds. Inspect its proposed spoken version with `python skills/filmcraft/scripts/film.py script skills/filmcraft/examples/booklet/film.json`. To build a voiced version, record the lines and retime the plan to that performance. The assembler also accepts real footage and bottom-half presenter clips. It does not generate a voice or character by itself.

[Research and its limits](skills/filmcraft/references/research.md) · [Forward tests and known limitations](EVALUATION.md) · [MIT license](LICENSE)
