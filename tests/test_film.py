"""Run from the repository root: python -m unittest discover -s tests."""
import copy
import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "filmcraft"
spec = importlib.util.spec_from_file_location("film", SKILL / "scripts" / "film.py")
film = importlib.util.module_from_spec(spec)
spec.loader.exec_module(film)
PLAN = json.loads((SKILL / "examples/booklet/film.json").read_text(encoding="utf-8"))
FF = shutil.which(os.environ.get("FILMCRAFT_FFMPEG", "ffmpeg"))


class PlanTests(unittest.TestCase):
    def test_booklet_runtime(self):
        self.assertEqual(film.validate(PLAN), 21)

    def test_broken_source_fails_at_scene(self):
        plan = copy.deepcopy(PLAN)
        plan["scenes"][2]["evidence"] = ["wrong-id"]
        with self.assertRaisesRegex(ValueError,"open: unknown source"):
            film.validate(plan)

    def test_qualification_in_notes_only_fails(self):
        plan = copy.deepcopy(PLAN)
        plan["scenes"][0].update(basis="proposal", screen_label="Proposed design",
                                 spoken_qualification="In this drawing")
        with self.assertRaisesRegex(ValueError,"actual recording copy"):
            film.validate(plan)

    def test_duplicate_id_and_subframe_timing(self):
        for update in ({"id":"proof"}, {"seconds":0.001}):
            with self.subTest(update=update):
                plan=copy.deepcopy(PLAN)
                plan["scenes"][1].update(update)
                with self.assertRaises(ValueError):
                    film.validate(plan)


@unittest.skipUnless(FF,"Set FILMCRAFT_FFMPEG or put ffmpeg on PATH to exercise media tests")
class MediaTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.src = self.root / "input.mp4"
        subprocess.run([FF,"-loglevel","error","-f","lavfi","-i","color=blue:s=160x96:r=24:d=1",
                        "-f","lavfi","-i","sine=frequency=440:duration=1","-c:v","libx264",
                        "-c:a","aac","-pix_fmt","yuv420p",str(self.src)],check=True)
        self.plan=copy.deepcopy(PLAN)
        self.plan["size"]=[160,192]
        self.plan["scenes"]=self.plan["scenes"][:1]
        self.scene=self.plan["scenes"][0]
        self.scene.update(file=self.src.name, seconds=0.5, audio="@presenter",
                          presenter=self.src.name, presenter_in=0.25, basis="proposal",
                          voice="This is a sketch.", spoken_qualification="a sketch",
                          screen_label="Sketch")

    def test_presenter_audio_label_and_safe_retry(self):
        out=self.root/"approved.mp4"
        film.validate(self.plan)
        film.render(FF,self.plan,self.root,out)
        before=out.read_bytes()
        self.assertGreater(len(before),500)
        with self.assertRaisesRegex(ValueError,"new output path"):
            film.render(FF,self.plan,self.root,out)
        self.assertEqual(out.read_bytes(),before)

    def test_truncated_second_stream_fails_without_final(self):
        mismatched=self.root/"short-audio.mkv"
        subprocess.run([FF,"-loglevel","error","-i",str(self.src),"-af","atrim=end=0.2",
                        "-c:v","copy","-c:a","pcm_s16le",str(mismatched)],check=True)
        self.scene.update(file=mismatched.name, audio="@picture")
        out=self.root/"short.mp4"
        with self.assertRaisesRegex(ValueError,"Media ends early"):
            film.render(FF,self.plan,self.root,out)
        self.assertFalse(out.exists())


if __name__=="__main__":
    unittest.main()
