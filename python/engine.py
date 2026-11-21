#!/usr/bin/env python3
"""CosmoFrames V1 deterministic Pillow renderer with streamed FFmpeg export."""
import json, math, shutil, subprocess, sys, time
from pathlib import Path
from PIL import Image, ImageColor, ImageDraw, ImageFont

VERSION = "1.0.0"
TYPES = {"text", "rectangle", "circle", "polygon", "image"}

def die(message, code=1):
    print("ERROR: " + str(message), file=sys.stderr)
    raise SystemExit(code)

def validate(p):
    def number(v, label, minimum=None, maximum=None):
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
            die(label + " must be a finite number.", 2)
        if minimum is not None and v < minimum: die(label + " must be >= " + str(minimum) + ".", 2)
        if maximum is not None and v > maximum: die(label + " must be <= " + str(maximum) + ".", 2)
    if not isinstance(p, dict): die("Project root must be an object.", 2)
    if p.get("version") != 1: die("version must equal 1.", 2)
    for key in ("output", "audio"):
        if key in p and (not isinstance(p[key], str) or not p[key].strip()): die(key + " must be a non-empty path string.", 2)
    def color(v, label):
        if not isinstance(v, str): die(label + " must be a CSS-style color string.", 2)
        try: ImageColor.getcolor(v, "RGBA")
        except ValueError: die(label + " is not a recognized color: " + v, 2)
    color(p.get("background", "#101018"), "background")
    r = p.get("resolution")
    if not isinstance(r, dict): die("resolution must be an object.", 2)
    for key in ("width", "height"):
        if isinstance(r.get(key), bool) or not isinstance(r.get(key), int) or not 1 <= r[key] <= 8192:
            die("resolution." + key + " must be an integer from 1 to 8192.", 2)
    number(p.get("fps", 30), "fps", 0.1, 60)
    number(p.get("duration", 5), "duration", 0.01, 600)
    if not isinstance(p.get("scenes"), list) or not p["scenes"]: die("scenes must be a non-empty array.", 2)
    allowed_animations = {"x", "y", "width", "height", "scale", "opacity", "rotation"}
    easings = {"linear", "ease-in", "ease-out", "ease-in-out"}
    for si, scene in enumerate(p["scenes"]):
        if not isinstance(scene, dict) or not isinstance(scene.get("elements", []), list): die("Invalid scene at index " + str(si), 2)
        for ei, el in enumerate(scene.get("elements", [])):
            label = "scenes[%d].elements[%d]" % (si, ei)
            if not isinstance(el, dict) or el.get("type") not in TYPES:
                die("Unsupported element at " + label + ". Supported: " + ", ".join(sorted(TYPES)), 2)
            for prop in ("x", "y", "start", "end", "fontSize", "radius", "width", "height", "scale", "opacity", "rotation"):
                if prop in el: number(el[prop], label + "." + prop, 0 if prop in ("start", "end", "fontSize", "radius", "width", "height", "scale") else None)
            if "end" in el and el["end"] <= el.get("start", 0): die(label + ".end must be greater than start.", 2)
            if el["type"] == "text" and not isinstance(el.get("text", ""), str): die(label + ".text must be a string.", 2)
            color(el.get("color", el.get("fill", "#ffffff")), label + ".color")
            if "strokeColor" in el: color(el["strokeColor"], label + ".strokeColor")
            if el["type"] == "image" and (not isinstance(el.get("src"), str) or not el["src"].strip()): die(label + ".src must be a non-empty path.", 2)
            if el["type"] == "polygon":
                pts = el.get("points")
                if not isinstance(pts, list) or len(pts) < 3 or any(not isinstance(pt, list) or len(pt) != 2 or any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in pt) for pt in pts):
                    die(label + ".points must contain at least three numeric [x, y] pairs.", 2)
            animations = el.get("animations", {})
            if not isinstance(animations, dict): die(label + ".animations must be an object.", 2)
            for prop, keys in animations.items():
                if prop not in allowed_animations: die(label + ".animations has unsupported property: " + str(prop), 2)
                if not isinstance(keys, list) or not keys: die(label + ".animations." + prop + " must be a non-empty keyframe array.", 2)
                previous = -1.0
                for ki, key in enumerate(keys):
                    if not isinstance(key, dict) or "time" not in key or "value" not in key: die(label + ".animations." + prop + "[" + str(ki) + "] needs time and value.", 2)
                    number(key["time"], label + ".animations." + prop + ".time", 0)
                    if key["time"] <= previous: die(label + ".animations." + prop + " keyframe times must be strictly increasing.", 2)
                    previous = key["time"]
                    number(key["value"], label + ".animations." + prop + ".value")
                    if prop == "opacity" and not 0 <= key["value"] <= 1: die(label + ".animations.opacity values must be between 0 and 1.", 2)
                    if prop == "scale" and key["value"] < 0: die(label + ".animations.scale values cannot be negative.", 2)
                    if key.get("easing", "linear") not in easings: die(label + ".animations." + prop + " has an unsupported easing.", 2)
            if "opacity" in el: number(el["opacity"], label + ".opacity", 0, 1)
            if el.get("anchor", "lt") not in {"lt", "mt", "rt", "lm", "mm", "rm", "lb", "mb", "rb"}:
                if el["type"] == "text": die(label + ".anchor is not a supported Pillow text anchor.", 2)
def load(path):
    try: p = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError: die("Project file not found: " + str(path))
    except json.JSONDecodeError as e: die("Invalid JSON line %d column %d: %s" % (e.lineno, e.colno, e.msg), 2)
    validate(p); p["_base"] = path.parent
    return p

def ease(name, t):
    t = max(0.0, min(1.0, t))
    if name == "ease-in": return t*t
    if name == "ease-out": return 1-(1-t)*(1-t)
    if name == "ease-in-out": return 3*t*t-2*t*t*t
    return t

def value(el, prop, default, t):
    keys = el.get("animations", {}).get(prop)
    if not keys: return default
    keys = sorted(keys, key=lambda k: float(k["time"]))
    if t <= float(keys[0]["time"]): return keys[0]["value"]
    if t >= float(keys[-1]["time"]): return keys[-1]["value"]
    for a,b in zip(keys, keys[1:]):
        ta,tb = float(a["time"]),float(b["time"])
        if ta <= t <= tb:
            f = ease(a.get("easing","linear"), (t-ta)/(tb-ta)) if tb != ta else 1
            av,bv = a["value"],b["value"]
            if isinstance(av,(int,float)) and isinstance(bv,(int,float)): return av+(bv-av)*f
            return av if f < 1 else bv
    return default

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
        f=get_font(int(float(el.get("fontSize",48))*scale),bool(el.get("bold",False)))
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
            im=Image.open(src).convert("RGBA")
            iw=int(el.get("width",im.width)*scale); ih=int(el.get("height",im.height)*scale)
            im=im.resize((max(1,iw),max(1,ih))); layer.alpha_composite(im,(int(x),int(y)))
        except Exception as e: die("Could not load image: "+str(e))
    if rotation: layer=layer.rotate(-rotation,resample=Image.Resampling.BICUBIC,center=(int(x),int(y)))
    if opacity<1: layer.putalpha(layer.getchannel("A").point(lambda a:int(a*opacity)))
    canvas.alpha_composite(layer)

def frame(p, index):
    w,h=p["resolution"]["width"],p["resolution"]["height"]; t=index/float(p.get("fps",30))
    canvas=Image.new("RGBA",(w,h),p.get("background","#101018"))
    for scene in p["scenes"]:
        for el in scene.get("elements",[]):
            start,end=float(el.get("start",0)),float(el.get("end",p.get("duration",5)))
            if start<=t<end: draw(canvas,el,t-start,p["_base"])
    return canvas.convert("RGB")

def render(p,path):
    ff=shutil.which("ffmpeg")
    if not ff: die("FFmpeg not found. Termux: pkg install ffmpeg")
    w,h=p["resolution"]["width"],p["resolution"]["height"]; fps=float(p.get("fps",30))
    count=math.ceil(float(p.get("duration",5))*fps)
    out=(path.parent/p.get("output","output.mp4")).resolve(); out.parent.mkdir(parents=True,exist_ok=True)
    cmd=[ff,"-y","-loglevel","error","-f","rawvideo","-pixel_format","rgb24","-video_size",str(w)+"x"+str(h),"-framerate",str(fps),"-i","-"]
    audio=p.get("audio")
    if audio:
        ap=(path.parent/audio).resolve()
        if not ap.is_file(): die("Audio file not found: "+str(ap))
        cmd += ["-i",str(ap),"-map","0:v:0","-map","1:a:0","-c:a","aac","-shortest"]
    else: cmd += ["-an"]
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

def main():
    if len(sys.argv)<2: die("Expected info/init/validate/preview/render",2)
    action=sys.argv[1]
    if action=="info":
        import PIL
        print("CosmoFrames "+VERSION+"\nPython "+sys.version.split()[0]+"\nPillow "+PIL.__version__+"\nFFmpeg "+str(shutil.which("ffmpeg") or "not found")+"\nChromium optional; V1 uses Pillow")
        return
    if action=="init":
        name=sys.argv[2] if len(sys.argv)>2 else "my-video"; folder=Path(name).resolve()
        if folder.exists(): die("Refusing to overwrite existing directory: "+str(folder),2)
        folder.mkdir(parents=True)
        sample={"version":1,"resolution":{"width":480,"height":854},"fps":24,"duration":5,"background":"#101018","output":"output.mp4","scenes":[{"elements":[{"type":"text","text":"Hello, CosmoFrames!","x":40,"y":360,"fontSize":36,"bold":True,"color":"#ffffff","animations":{"y":[{"time":0,"value":450,"easing":"ease-out"},{"time":1,"value":360}],"opacity":[{"time":0,"value":0},{"time":0.7,"value":1}]}},{"type":"circle","x":240,"y":240,"radius":65,"color":"#20d9e8","animations":{"scale":[{"time":0,"value":0.1},{"time":1,"value":1}]}}]}]}
        (folder/"project.json").write_text(json.dumps(sample,indent=2),encoding="utf-8")
        print("Created "+str(folder/"project.json")); return
    if len(sys.argv)<3: die(action+" requires a project JSON path.",2)
    path=Path(sys.argv[2]).resolve(); p=load(path)
    if action=="validate":
        print("Valid project: %s | %dx%d | %s FPS | %s sec" % (path,p["resolution"]["width"],p["resolution"]["height"],p.get("fps",30),p.get("duration",5)))
    elif action=="preview":
        at=0.0
        if "--time" in sys.argv:
            try: at=float(sys.argv[sys.argv.index("--time")+1])
            except (ValueError,IndexError): die("--time requires a numeric value.")
        idx=max(0,min(math.ceil(p.get("duration",5)*p.get("fps",30))-1,int(at*p.get("fps",30))))
        dest=path.parent/"preview.png"; frame(p,idx).save(dest); print("Saved "+str(dest))
    elif action=="render": render(p,path)
    else: die("Unknown action: "+action,2)

if __name__=="__main__": main()
