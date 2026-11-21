"""Scene transition timing helpers."""

def scene_opacity(scene, local_time):
    transition = scene.get("transition_in")
    if not transition:
        return 1.0
    duration = float(transition.get("duration", 0))
    if duration <= 0:
        return 1.0
    progress = max(0.0, min(1.0, local_time / duration))
    kind = transition.get("type", "fade")
    if kind == "fade":
        return progress
    return 1.0
