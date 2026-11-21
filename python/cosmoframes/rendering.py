"""Pillow drawing and streamed FFmpeg MP4 rendering."""
import math, shutil, subprocess, sys, time
from functools import lru_cache
from pathlib import Path
from PIL import Image, ImageColor, ImageDraw, ImageFont
from .animation import value
from .errors import die
from .transitions import scene_opacity
from .compositing import apply_mask, composite

@lru_cache(maxsize=8)
def _gradient_cached(size, colors, angle):
    colors = [ImageColor.getrgb(c) for c in colors]
    strip = Image.new("RGB", (256, 1))
    pixels = []
    for x in range(256):
        pos = x / 255 * (len(colors) - 1)
        index = min(len(colors) - 2, int(pos))
        f = pos - index
        a, b = colors[index], colors[index + 1]
        pixels.append(tuple(int(a[i] + (b[i] - a[i]) * f) for i in range(3)))
    strip.putdata(pixels)
    if angle:
        strip = strip.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True)
    return strip.resize(size, Image.Resampling.BICUBIC).convert("RGBA")

def gradient_image(size, spec):
    colors = tuple(spec["colors"])
    return _gradient_cached(tuple(size), colors, float(spec.get("angle", 0))).copy()

@lru_cache(maxsize=8)
def load_asset(path):
    with Image.open(path) as source:
        return source.convert("RGBA")


@lru_cache(maxsize=64)
def get_font(size, bold=False):
    paths = ["/system/fonts/Roboto-Bold.ttf","/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"] if bold else ["/system/fonts/Roboto-Regular.ttf","/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    for path in paths:
        try: return ImageFont.truetype(path, size=max(1,size))
        except OSError: pass
    return ImageFont.load_default()

def draw(canvas, el, t, base):
    x,y = float(value(el,"x",el.get("x",0),t)),float(value(el,"y",el.get("y",0),t))
    scale = float(value(el,"scale",el.get("scale",1),t))
    opacity = max(0,min(1,float(value(el,"opacity",el.get("opacity",1),t))))
    rotation = float(value(el,"rotation",el.get("rotation",0),t))
    layer = Image.new("RGBA",canvas.size,(0,0,0,0)); d=ImageDraw.Draw(layer)
    fill=el.get("color",el.get("fill","#ffffff")); typ=el["type"]
    if typ=="text":
        f=get_font(int(float(value(el,"fontSize",el.get("fontSize",48),t))*scale),bool(el.get("bold",False)))
        d.text((x,y),str(el.get("text","")),font=f,fill=fill,anchor=el.get("anchor","lt"),stroke_width=int(el.get("strokeWidth",0)),stroke_fill=el.get("strokeColor","#000000"))
    elif typ=="rectangle":
        w=float(value(el,"width",el.get("width",100),t))*scale
        h=float(value(el,"height",el.get("height",100),t))*scale
        d.rounded_rectangle((x,y,x+w,y+h),radius=int(el.get("radius",0)*scale),fill=fill)
    elif typ=="circle":
        r=float(el.get("radius",50))*scale; d.ellipse((x-r,y-r,x+r,y+r),fill=fill)
    elif typ=="polygon":
        pts=[(x+float(a)*scale,y+float(b)*scale) for a,b in el.get("points",[])]
        if len(pts)<3: die("Polygon needs at least three [x,y] points.")
        d.polygon(pts,fill=fill)
    elif typ=="image":
        src=(base/str(el.get("src",""))).resolve()
        if not src.is_file(): die("Image asset not found: "+str(src))
        try:
            im=load_asset(str(src))
            iw=int(float(value(el,"width",el.get("width",im.width),t))*scale); ih=int(float(value(el,"height",el.get("height",im.height),t))*scale)
            im=im.resize((max(1,iw),max(1,ih))); layer.alpha_composite(im,(int(x),int(y)))
        except Exception as e: die("Could not load image: "+str(e))
    if "gradient" in el:
        gradient = gradient_image(canvas.size, el["gradient"])
        gradient.putalpha(layer.getchannel("A"))
        layer = gradient
    if rotation:
        bounds = layer.getbbox()
        if bounds:
            center = ((bounds[0] + bounds[2]) / 2, (bounds[1] + bounds[3]) / 2)
            layer = layer.rotate(-rotation, resample=Image.Resampling.BICUBIC, center=center)
    if opacity<1: layer.putalpha(layer.getchannel("A").point(lambda a:int(a*opacity)))
    try:
        layer = apply_mask(layer, el.get("mask"), base)
        composite(canvas, layer, el.get("blend_mode", "normal"))
    except ValueError as exc:
        die(str(exc))

def frame(p, index):
    w,h=p["resolution"]["width"],p["resolution"]["height"]; t=index/float(p.get("fps",30))
    canvas=gradient_image((w,h),p["background_gradient"]) if "background_gradient" in p else Image.new("RGBA",(w,h),p.get("background","#101018"))
    for scene in p["scenes"]:
        scene_start = float(scene.get("start", 0))
        scene_end = float(scene.get("end", p.get("duration", 5)))
        local_time = t - scene_start
        if not scene_start <= t < scene_end:
            continue
        scene_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        for el in scene.get("elements", []):
            start, end = float(el.get("start", 0)), float(el.get("end", scene_end - scene_start))
            if start <= local_time < end:
                draw(scene_layer, el, local_time - start, p["_base"])
        opacity = scene_opacity(scene, local_time)
        if opacity < 1:
            scene_layer.putalpha(scene_layer.getchannel("A").point(lambda a: int(a * opacity)))
        composite(canvas, scene_layer, scene.get("blend_mode", "normal"))
    return canvas.convert("RGB")

def render(p,path):
    ff=shutil.which("ffmpeg")
    if not ff: die("FFmpeg not found. Termux: pkg install ffmpeg")
    w,h=p["resolution"]["width"],p["resolution"]["height"]; fps=float(p.get("fps",30))
    count=math.ceil(float(p.get("duration",5))*fps)
    out=(path.parent/p.get("output","output.mp4")).resolve(); out.parent.mkdir(parents=True,exist_ok=True)
    cmd=[ff,"-y","-loglevel","error","-f","rawvideo","-pixel_format","rgb24","-video_size",str(w)+"x"+str(h),"-framerate",str(fps),"-i","-"]
    tracks = list(p.get("audio_tracks", []))
    if p.get("audio"):
        tracks.insert(0, {"src": p["audio"], "start": 0, "volume": 1})
    if tracks:
        filters = []
        labels = []
        for i, track in enumerate(tracks):
            ap = (path.parent / track["src"]).resolve()
            if not ap.is_file(): die("Audio file not found: " + str(ap))
            cmd += ["-i", str(ap)]
            delay = int(float(track.get("start", 0)) * 1000)
            volume = float(track.get("volume", 1))
            label = "a%d" % i
            filters.append("[%d:a]atrim=duration=%s,asetpts=PTS-STARTPTS,adelay=%d:all=1,volume=%s[%s]" % (i + 1, p.get("duration", 5), delay, volume, label))
            labels.append("[%s]" % label)
        if len(labels) == 1:
            filters.append("%sanull[aout]" % labels[0])
        else:
            filters.append("%samix=inputs=%d:duration=longest:dropout_transition=0[aout]" % ("".join(labels), len(labels)))
        cmd += ["-filter_complex", ";".join(filters), "-map", "0:v:0", "-map", "[aout]", "-c:a", "aac"]
    else:
        cmd += ["-an"]
    cmd += ["-c:v","libx264","-preset",p.get("preset","ultrafast"),"-pix_fmt","yuv420p","-movflags","+faststart","-t",str(p.get("duration",5)),str(out)]
    print("Rendering %d frames at %dx%d %.2f FPS" % (count,w,h,fps))
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    started=time.time()
    try:
        for i in range(count):
            proc.stdin.write(frame(p,i).tobytes())
            if i and i%max(1,int(fps*2))==0: print("Progress: %d/%d frames" % (i,count),file=sys.stderr)
        proc.stdin.close(); code=proc.wait()
    except (BrokenPipeError,OSError) as e:
        proc.kill(); die("FFmpeg stream failed: "+str(e))
    if code: die("FFmpeg failed with exit code "+str(code))
    if not out.is_file() or out.stat().st_size==0: die("No output MP4 was created.")
    print("Created %s (%d bytes) in %.1fs" % (out,out.stat().st_size,time.time()-started))
