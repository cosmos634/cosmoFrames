"""Layer masks and blend-mode compositing."""
from PIL import Image, ImageChops

BLEND_MODES = {"normal", "multiply", "screen", "add", "overlay"}

def apply_mask(layer, mask_spec, base):
    if not mask_spec:
        return layer
    if not isinstance(mask_spec, dict) or not isinstance(mask_spec.get("src"), str):
        raise ValueError("mask must contain a source image path")
    path = (base / mask_spec["src"]).resolve()
    if not path.is_file():
        raise ValueError("Mask image not found: " + str(path))
    with Image.open(path) as source:
        mask = source.convert("L").resize(layer.size, Image.Resampling.LANCZOS)
    if mask_spec.get("invert", False):
        mask = ImageChops.invert(mask)
    alpha = ImageChops.multiply(layer.getchannel("A"), mask)
    result = layer.copy()
    result.putalpha(alpha)
    return result

def composite(destination, source, mode="normal"):
    if mode not in BLEND_MODES:
        raise ValueError("Unsupported blend mode: " + str(mode))
    if mode == "normal":
        destination.alpha_composite(source)
        return
    dst = destination.convert("RGB")
    src = source.convert("RGB")
    if mode == "multiply":
        blended = ImageChops.multiply(dst, src)
    elif mode == "screen":
        blended = ImageChops.screen(dst, src)
    elif mode == "add":
        blended = ImageChops.add(dst, src)
    else:
        low = ImageChops.add(ImageChops.multiply(dst, src), ImageChops.multiply(dst, src))
        screen = ImageChops.screen(dst, src)
        high = ImageChops.add(screen, screen, scale=1, offset=-255)
        luminance = dst.convert("L").point(lambda value: 255 if value >= 128 else 0)
        blended = Image.composite(high, low, luminance)
    alpha = source.getchannel("A")
    mixed = Image.composite(blended, dst, alpha)
    out = Image.alpha_composite(destination, source)
    out.paste(mixed, (0, 0))
    destination.paste(out)
