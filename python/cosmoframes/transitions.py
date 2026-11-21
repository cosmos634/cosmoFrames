"""Deterministic scene transition masks."""
from PIL import Image, ImageDraw, ImageChops

TRANSITION_TYPES = {"fade", "wipe_left", "wipe_right", "wipe_up", "wipe_down"}


def _progress(spec, elapsed):
    duration = float(spec.get("duration", 0))
    if duration <= 0:
        return 1.0
    return max(0.0, min(1.0, elapsed / duration))


def _mask(size, kind, progress):
    width, height = size
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    if kind == "fade":
        mask.paste(int(round(progress * 255)), (0, 0, width, height))
    elif kind == "wipe_left":
        draw.rectangle((0, 0, int(round(width * progress)), height), fill=255)
    elif kind == "wipe_right":
        edge = int(round(width * (1 - progress)))
        draw.rectangle((edge, 0, width, height), fill=255)
    elif kind == "wipe_up":
        draw.rectangle((0, 0, width, int(round(height * progress))), fill=255)
    elif kind == "wipe_down":
        edge = int(round(height * (1 - progress)))
        draw.rectangle((0, edge, width, height), fill=255)
    return mask


def apply_scene_transitions(layer, scene, local_time, scene_duration):
    alpha = layer.getchannel("A")
    incoming = scene.get("transition_in")
    if incoming:
        kind = incoming.get("type", "fade")
        alpha = ImageChops.multiply(alpha, _mask(layer.size, kind, _progress(incoming, local_time)))
    outgoing = scene.get("transition_out")
    if outgoing:
        elapsed = scene_duration - local_time
        kind = outgoing.get("type", "fade")
        alpha = ImageChops.multiply(alpha, _mask(layer.size, kind, _progress(outgoing, elapsed)))
    layer.putalpha(alpha)
    return layer
