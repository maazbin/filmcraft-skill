"""Check a Filmcraft plan, extract the script, or assemble its local media."""
import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def number(value):
    return type(value) in (int, float) and math.isfinite(value)


def required_text(record, key, location):
    value = record.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{location}: provide text for {key}")
    return value


def validate(plan):
    if not isinstance(plan, dict):
        raise ValueError("Plan must be a JSON object")
    required_text(plan, "title", "film")
    size = plan.get("size")
    if not isinstance(size, list) or len(size) != 2 or any(type(x) is not int or x < 2 or x % 2 for x in size):
        raise ValueError("size must contain two positive even pixel dimensions")
    fps = plan.get("fps")
    if type(fps) is not int or not 1 <= fps <= 120:
        raise ValueError("fps must be an integer from 1 to 120")
    sources = plan.get("sources", {})
    if not isinstance(sources, dict) or any(not isinstance(v, str) or not v.strip() for v in sources.values()):
        raise ValueError("sources must map IDs to source descriptions")
    scenes = plan.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        raise ValueError("Add at least one scene")
    ids = set()
    for index, scene in enumerate(scenes, 1):
        if not isinstance(scene, dict):
            raise ValueError(f"Scene {index} must be an object")
        key = required_text(scene, "id", f"scene {index}")
        if key in ids:
            raise ValueError(f"Duplicate scene ID: {key}")
        ids.add(key)
        for name in ("picture", "change", "sound"):
            required_text(scene, name, key)
        seconds = scene.get("seconds")
        if not number(seconds) or seconds <= 0 or abs(seconds * fps - round(seconds * fps)) > .00001:
            raise ValueError(f"{key}: duration must be positive and land on a frame at {fps} fps")
        if not isinstance(scene.get("voice"), str):
            raise ValueError(f"{key}: supply voice text or an empty string for silence")
        basis = scene.get("basis")
        if basis not in ("documented", "proposal", "fiction", "observation", "transition"):
            raise ValueError(f"{key}: choose a documented, proposal, fiction, observation or transition basis")
        if basis == "proposal":
            required_text(scene, "screen_label", key)
            if scene["voice"] and required_text(scene, "spoken_qualification", key) not in scene["voice"]:
                raise ValueError(f"{key}: spoken_qualification must appear in the actual recording copy")
        refs = scene.get("evidence", [])
        if not isinstance(refs, list) or any(not isinstance(x, str) or x not in sources for x in refs):
            raise ValueError(f"{key}: unknown source ID in evidence")
        if (scene.get("factual") is True or basis in ("documented", "proposal", "observation")) and not refs:
            raise ValueError(f"{key}: mark the evidence for the factual beat")
        if "factual" in scene and type(scene["factual"]) is not bool:
            raise ValueError(f"{key}: factual must be true or false")
        for name in ("in", "presenter_in", "audio_in"):
            value = scene.get(name, 0)
            if not number(value) or value < 0:
                raise ValueError(f"{key}: {name} must be a nonnegative number")
        for name in ("file", "audio", "presenter"):
            if scene.get(name) is not None:
                required_text(scene, name, key)
        if scene.get("audio") == "@presenter" and not scene.get("presenter"):
            raise ValueError(f"{key}: @presenter requires a presenter clip")
        if scene.get("audio") in ("@presenter", "@picture") and "audio_in" in scene:
            raise ValueError(f"{key}: linked audio follows its clip in-point, remove audio_in")
    return sum(round(s["seconds"] * fps) for s in scenes) / fps


def run(args, cwd=None):
    result = subprocess.run(args, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8", errors="replace")
    if result.returncode:
        raise ValueError(result.stderr.strip() or f"Command failed: {args[0]}")
    return result


def media_path(root, name):
    if not name:
        raise ValueError("The shot needs an actual file for rendering")
    path = (root / name).resolve()
    if not path.is_file():
        raise ValueError(f"Media missing: {path}")
    return str(path)


STILLS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}


def inspect_media(ff, path, stream, start, duration):
    result = subprocess.run([ff, "-hide_banner", "-i", path], capture_output=True, encoding="utf-8", errors="replace")
    info = result.stderr
    if not re.search(r"Stream #.*?: " + stream + ":", info):
        raise ValueError(f"No {stream.lower()} stream in {path}")
    match = re.search(r"Duration: (\d+):(\d+):([\d.]+)", info)
    if not match:
        raise ValueError(f"No usable duration for {path}; supply a seekable local clip")
    h, m, s = match.groups()
    if 3600 * int(h) + 60 * int(m) + float(s) + .015 < start + duration:
        raise ValueError(f"{path}: need {start + duration:.3f}s through end of selected interval")


def render_scene(ff, root, film, scene, segment):
    w, h = film["size"]
    rate, sec = film["fps"], scene["seconds"]
    args = [ff, "-nostdin", "-hide_banner", "-loglevel", "error", "-y"]
    src = media_path(root, scene.get("file"))
    start = scene.get("in", 0)
    if Path(src).suffix.lower() in STILLS:
        if start:
            raise ValueError("A still has no source in-point")
        args += ["-loop", "1", "-framerate", str(rate)]
    else:
        inspect_media(ff, src, "Video", start, sec)
        args += ["-ss", str(start)]
    args += ["-i", src]
    presenter = scene.get("presenter")
    panel = h // 4 * 2 if presenter else h
    fit = f"scale={w}:{panel}:force_original_aspect_ratio=decrease,pad={w}:{panel}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={rate},setpts=PTS-STARTPTS"
    filters = "[0:v:0]" + fit + "[picture]"
    video = "[picture]"
    if presenter:
        path = media_path(root, presenter)
        offset = scene.get("presenter_in", 0)
        inspect_media(ff, path, "Video", offset, sec)
        args += ["-ss", str(offset), "-i", path]
        filters += f";[1:v:0]scale={w}:{h-panel}:force_original_aspect_ratio=decrease,pad={w}:{h-panel}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={rate},setpts=PTS-STARTPTS[host];[picture][host]vstack=shortest=1[v]"
        video = "[v]"
    audio = scene.get("audio")
    idx = 2 if presenter else 1
    if audio in ("@presenter", "@picture"):
        matched = audio == "@presenter"
        inspect_media(ff, path if matched else src, "Audio", offset if matched else start, sec)
        idx = 1 if matched else 0
    elif audio:
        path = media_path(root, audio)
        offset = scene.get("audio_in", 0)
        inspect_media(ff, path, "Audio", offset, sec)
        args += ["-ss", str(offset), "-i", path]
    else:
        args += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]
    if scene.get("screen_label"):
        label = required_text(scene, "screen_label", scene["id"])
        (segment.parent / "label.txt").write_text(label, encoding="utf-8")
        filters += (f";{video}drawtext=textfile=label.txt:expansion=none:fontsize={max(14,h//28)}:"
                    "fontcolor=white:box=1:boxcolor=black@0.8:boxborderw=8:x=w*0.05:y=h*0.055[labelled]")
        video = "[labelled]"
    args += ["-filter_complex", filters, "-map", video, "-map", f"{idx}:a:0",
             "-t", str(sec), "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
             "-pix_fmt", "yuv420p", "-c:a", "pcm_s16le", "-ac", "2", "-ar", "48000", str(segment)]
    run(args, cwd=segment.parent)
    # Containers can outlast an individual stream. Count finished video packets
    # (one per H.264 frame) and stereo 16-bit PCM bytes before concatenation.
    packet_list = run([ff, "-loglevel", "error", "-i", str(segment), "-map", "0:v:0",
                       "-map", "0:a:0", "-c", "copy", "-f", "framecrc", "-"]).stdout
    frame_count = 0
    pcm_bytes = 0
    for line in packet_list.splitlines():
        fields = line.split(",")
        if fields[0] == "0":
            frame_count += 1
        elif fields[0] == "1":
            pcm_bytes += int(fields[4])
    if frame_count != round(sec * rate) or abs(pcm_bytes / 4 - sec * 48000) > 2:
        raise ValueError(f"Media ends early or exceeds the cut: got {frame_count} frames and "
                         f"{pcm_bytes / 192000:.3f}s audio. Adjust the cut or supply full-length media.")


def render(ff, plan, root, target):
    if target.exists():
        raise ValueError(f"Choose a new output path: {target}")
    if target.suffix.lower() != ".mp4":
        raise ValueError("Choose an .mp4 output path")
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=target.parent) as tmp:
        folder = Path(tmp)
        playlist = []
        for i, scene in enumerate(plan["scenes"]):
            segment = folder / f"shot-{i:05}.mkv"
            try:
                render_scene(ff, root, plan, scene, segment)
            except ValueError as exc:
                raise ValueError(f"{scene['id']}: {exc}") from exc
            playlist.append(f"file '{segment.name}'\nduration {scene['seconds']:.9f}")
        listing = folder / "cuts.txt"
        listing.write_text("\n".join(playlist) + "\n", encoding="utf-8")
        out = folder / "assembled.mp4"
        run([ff, "-loglevel", "error", "-f", "concat", "-safe", "1", "-i", str(listing),
             "-map", "0:v", "-map", "0:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
             "-movflags", "+faststart", str(out)])
        run([ff, "-loglevel", "error", "-xerror", "-i", str(out), "-map", "0:v", "-map", "0:a", "-f", "null", "-"])
        try:
            os.link(out, target)
        except FileExistsError:
            raise ValueError(f"Output appeared during render: {target}")
        except OSError:
            with target.open("xb") as saved:
                try:
                    with out.open("rb") as finished:
                        shutil.copyfileobj(finished, saved)
                except OSError:
                    saved.close()
                    target.unlink()
                    raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    for name in ("check", "script", "render"):
        cmd = sub.add_parser(name)
        cmd.add_argument("plan", type=Path)
        if name == "render":
            cmd.add_argument("output", type=Path)
            cmd.add_argument("--ffmpeg", default="ffmpeg")
    args = parser.parse_args()
    try:
        plan = json.loads(args.plan.read_text(encoding="utf-8-sig"))
        duration = validate(plan)
        if args.action == "check":
            print(f"{len(plan['scenes'])} scenes, {duration:.3f}s planned. Editorial review is separate.")
        elif args.action == "script":
            print("\n\n".join(s["voice"] for s in plan["scenes"] if s["voice"].strip()))
        else:
            ff = shutil.which(args.ffmpeg)
            if not ff:
                raise ValueError("Install FFmpeg or use --ffmpeg PATH")
            render(ff, plan, args.plan.parent, args.output.resolve())
            print(args.output.resolve())
    except (OSError, ValueError) as exc:
        parser.exit(1, f"filmcraft: {exc}\n")


if __name__ == "__main__":
    main()
