"""Generate original moving booklet diagrams and paper foley for the included film plan."""
import argparse
import array
from functools import lru_cache
import json
import math
from pathlib import Path
import random
import shutil
import subprocess
import sys
import wave

from PIL import Image, ImageDraw, ImageFont


W, H = 960, 540
INK, PAPER, LIME, MINT = "#202a2b", "#f4eedc", "#cae679", "#aacbc1"
FONT_PATHS = {
    "bold": ["DejaVuSans-Bold.ttf", "arialbd.ttf", "/System/Library/Fonts/Supplemental/Arial Bold.ttf"],
    "serif": ["DejaVuSerif.ttf", "georgia.ttf", "/System/Library/Fonts/Supplemental/Georgia.ttf"],
    "sans": ["DejaVuSans.ttf", "arial.ttf", "/System/Library/Fonts/Supplemental/Arial.ttf"],
}


@lru_cache(maxsize=36)
def font(style, size):
    for candidate in FONT_PATHS[style]:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            pass
    return ImageFont.load_default(size=size)


def ease(t):
    t = min(1, max(0, t))
    return t*t*(3-2*t)


def letters(draw, point, text, size, color, face="sans", anchor="la"):
    draw.text(point, text, font=font(face, size), fill=color, anchor=anchor)


@lru_cache(maxsize=12)
def leaf(num, label, tone):
    page = Image.new("RGB", (205, 252), tone)
    d = ImageDraw.Draw(page)
    d.rectangle((9, 9, 195, 242), outline=INK, width=1)
    letters(d, (20, 23), "FOLD STUDY", 12, INK, "bold")
    letters(d, (103, 119), str(num), 89, INK, "serif", "mm")
    d.line((20, 197, 185, 197), fill=INK)
    letters(d, (20, 208), label, 15, INK, "bold")
    return page


def render_frame(scene, t):
    index = ["proof","fold","open","end"].index(scene)
    image = Image.new("RGB", (W,H), INK)
    d = ImageDraw.Draw(image)
    letters(d, (45, 26), "FIELD NOTES     /     PRINT", 15, LIME, "bold")
    letters(d, (915, 26), "BOOKLET STUDY", 14, PAPER, "sans", "ra")
    d.line((45,62,915,62), fill="#657270")
    titles = ["A mistake on the proof?", "Follow the fold.", "Inside the booklet", "Ready for the printer."]
    letters(d, (45,75), titles[index], 44, PAPER, "serif")
    cover = scene != "open"
    fold = ease((t-.5)/2.3) if scene=="fold" else 1-ease((t-.1)/1.45) if scene=="end" else 0
    left = leaf(16 if cover else 8,"BACK COVER" if scene=="end" else "OUTSIDE" if cover else "CENTRE", MINT if cover else PAPER)
    right = leaf(1 if cover else 9,"FRONT COVER" if scene=="end" else "OUTSIDE" if cover else "CENTRE",LIME if cover else PAPER)
    spine = 484
    y = 143
    span = 205 * math.cos(math.pi*fold)
    if span>1:
        height=round(252+16*math.sin(math.pi*fold))
        width=max(1,round(span))
        shown=left.resize((width,height),Image.Resampling.LANCZOS)
        x=spine-width
        d.rectangle((x+4,y+7,spine+205+5,y+258),fill="#11191b")
        image.paste(shown,(x,y-(height-252)//2))
    image.paste(right,(spine,y))
    d.line((spine,y,spine,y+251), fill="#53615b",width=2)
    if scene=="fold" and t>3.0:
        d.line((spine-88,y+133,spine-9,y+133),fill=MINT,width=2)
        letters(d,(spine-96,y+131),"16 is behind 1",18,MINT,"sans","rm")
    notes = ["On the flat sheet: page 16 next to page 1.",
             "Page 1 stays in front. Page 16 folds behind it.",
             "Pages 8 and 9 meet in the middle.",
             "The first and last pages share the outside sheet."]
    letters(d,(W//2,442),notes[index],25,PAPER,"sans","mm")
    d.line((45,485,915,485),fill="#657270")
    for j in range(4):
        d.rectangle((45+j*22,502,59+j*22,505), fill=LIME if j<=index else "#657270")
    letters(d,(915,497),"ORIGINAL DIAGRAM   /   LEFT-BOUND, 16 PAGES",12,MINT,"sans","ra")
    return image


def foley(path, seconds, number):
    rate=24000
    rng=random.Random(120+number)
    buf=array.array("h")
    last=0.0
    for i in range(round(seconds*rate)):
        t=i/rate
        noise=rng.uniform(-1,1)
        env=math.exp(-((t-(.6 if number!=1 else 1.65))/.19)**2)
        signal=(noise-last)*.06*env
        last=noise
        buf.append(round(signal*32767))
    if sys.byteorder!="little":
        buf.byteswap()
    with wave.open(str(path),"wb") as audio:
        audio.setparams((1,2,rate,0,"NONE","not compressed"))
        audio.writeframes(buf.tobytes())


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("folder",type=Path)
    p.add_argument("--ffmpeg",default="ffmpeg")
    args=p.parse_args()
    ff=shutil.which(args.ffmpeg)
    if not ff:
        p.error("Install FFmpeg or supply --ffmpeg PATH")
    dest=args.folder.resolve()
    if dest.exists() and any(dest.iterdir()):
        p.error("Choose an empty production folder")
    media=dest/"media"
    media.mkdir(parents=True,exist_ok=True)
    template=Path(__file__).with_name("film.json")
    shutil.copyfile(template,dest/"film.json")
    plan=json.loads(template.read_text(encoding="utf-8"))
    for j,s in enumerate(plan["scenes"]):
        cmd=[ff,"-nostdin","-loglevel","error","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}",
             "-framerate",str(plan["fps"]),"-i","pipe:0","-an","-c:v","libx264","-preset","veryfast",
             "-crf","17","-pix_fmt","yuv420p",str(dest/s["file"])]
        with subprocess.Popen(cmd,stdin=subprocess.PIPE) as enc:
            for k in range(round(s["seconds"]*plan["fps"])):
                enc.stdin.write(render_frame(s["id"],k/plan["fps"]).tobytes())
            enc.stdin.close()
            if enc.wait():
                raise SystemExit("Video encoder failed")
        foley(dest/s["audio"],s["seconds"],j)
    print(dest/"film.json")


if __name__=="__main__":
    main()
