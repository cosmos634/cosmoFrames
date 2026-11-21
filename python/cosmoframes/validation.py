"""Project schema and value validation."""
import math
from PIL import ImageColor
from .errors import die

TYPES = {"text", "rectangle", "circle", "polygon", "image"}

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
        for prop in ("start", "end"):
            if prop in scene: number(scene[prop], "scenes[%d].%s" % (si, prop), 0)
        if "end" in scene and scene["end"] <= scene.get("start", 0): die("scenes[%d].end must be greater than start." % si, 2)
        transition = scene.get("transition_in")
        if transition is not None:
            if not isinstance(transition, dict): die("scenes[%d].transition_in must be an object." % si, 2)
            if transition.get("type", "fade") != "fade": die("Only fade scene transitions are supported in this version.", 2)
            number(transition.get("duration", 0), "scenes[%d].transition_in.duration" % si, 0, 30)
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
