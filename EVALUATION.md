# What we tested

These are small forward tests with specific source packets. They are useful for reproducing a failure; they are not a guarantee that a model will write or direct well on another subject.

## Documentary trial

An independent agent received a 35-second commission about why a library stopped stamping return dates. It had a dated card, footage of a stamp beside a scanner, and four seconds of a librarian saying “I still keep it in this drawer.” No source gave a reason. The draft used the actual four-second tape and ended with the cause unresolved. Its cut to a neutral frame under the quote avoided implying that “it” referred to the stamp. One proposed sentence nevertheless treated the date as definitively a due date. We added explicit checks for the meaning of the date and for ambiguous referents across cuts.

## Lightweight model trial

A GPT-6 Luna agent at low reasoning effort received a 40-second animated explainer brief about an untested umbrella drip tray. It produced a clean read, timed shots and a pickup note acknowledging the lack of tests. The spoken film still asserted the tray caught the water. A second brief about a sketched window latch produced another overclaim: the first draft assigned red and green to states although the brief only specified a colored flag.

We added a fill-in pattern, a separate sound-off check, and fields for the **literal qualification in the recording copy** and a **visible label**. On retry, the same agent identified the image as a pencil drawing, expressed the flag as the inventor’s intention, and ended with the test still outstanding. Its opening label was “DESIGN SKETCH.” This was a guided retry, not a blind benchmark. The validator verifies presence and source IDs; the editor must still judge whether words and pictures mislead.

**Use the two briefs as a regression exercise.** Hide project notes and inspect only the lines and shot labels the viewer receives. Would they infer a cause, result or safety claim that the source cannot establish?

## Production checks

Run `python -m unittest discover -s tests -v` from the repository root. The suite checks the example duration, unknown sources, incomplete qualifications, duplicate IDs, non-frame durations, an actual labeled presenter cut with synchronized source audio, an early-ending audio stream, and preserving an existing output. Media tests require FFmpeg on PATH or in the FILMCRAFT_FFMPEG environment variable. The booklet exercise runs offline after installing dependencies.

The published 21-second example is an original moving diagram with a stereo sound track. Its four scene images and the complete decode were inspected. The five-minute archival essay is a writing and preproduction example, not a rendered documentary. No paid voice or avatar provider was exercised in these tests.
