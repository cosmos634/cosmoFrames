"""Deterministic keyframe interpolation and easing."""
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
