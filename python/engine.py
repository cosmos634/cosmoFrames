#!/usr/bin/env python3
"""CosmoFrames command-line entry point."""
import json, math, shutil, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import PIL
from cosmoframes.animation import ease, value
from cosmoframes.errors import die
from cosmoframes.rendering import frame, render
from cosmoframes.profiling import benchmark
from cosmoframes.validation import validate

VERSION = "1.0.0"

def load(path):
    try: p = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError: die("Project file not found: " + str(path))
    except json.JSONDecodeError as e: die("Invalid JSON line %d column %d: %s" % (e.lineno, e.colno, e.msg), 2)
    validate(p); p["_base"] = path.parent
    return p

def main():
    if len(sys.argv)<2: die("Expected info/init/validate/preview/render",2)
    action=sys.argv[1]
    if action=="info":
        import PIL
        print("CosmoFrames "+VERSION+"\nPython "+sys.version.split()[0]+"\nPillow "+PIL.__version__+"\nFFmpeg "+str(shutil.which("ffmpeg") or "not found")+"\nRenderer: Pillow CPU default\nBrowser: optional Chromium/CDP via playwright-core")
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
    elif action=="benchmark":
        count = None
        if "--frames" in sys.argv:
            try: count = int(sys.argv[sys.argv.index("--frames") + 1])
            except (ValueError, IndexError): die("--frames requires a positive integer.", 2)
            if count <= 0: die("--frames must be greater than zero.", 2)
        benchmark(p, count)
    else: die("Unknown action: "+action,2)

if __name__ == "__main__": main()
