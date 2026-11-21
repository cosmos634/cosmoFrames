"""Layer masks and alpha-aware CPU blend-mode compositing."""
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
    result = layer.copy()
    result.putalpha(ImageChops.multiply(result.getchannel("A"), mask))
    return result


def _blend_rgb(destination, source, mode):
    if mode == "multiply":
        return ImageChops.multiply(destination, source)
    if mode == "screen":
        return ImageChops.screen(destination, source)
    if mode == "add":
        return ImageChops.add(destination, source)
    channels = []
    for dst, src in zip(destination.split(), source.split()):
        low = ImageChops.multiply(dst, src).point(lambda value: min(255, value * 2))
        inverse_product = ImageChops.multiply(ImageChops.invert(dst), ImageChops.invert(src))
        high = ImageChops.invert(inverse_product.point(lambda value: min(255, value * 2)))
        threshold = dst.point(lambda value: 255 if value >= 128 else 0)
        channels.append(Image.composite(high, low, threshold))
    return Image.merge("RGB", channels)


def composite(destination, source, mode="normal"):
    if mode not in BLEND_MODES:
        raise ValueError("Unsupported blend mode: " + str(mode))
    if mode == "normal":
        destination.alpha_composite(source)
        return
    dst_rgba = destination.convert("RGBA")
    src_rgba = source.convert("RGBA")
    dst_rgb = dst_rgba.convert("RGB")
    src_rgb = src_rgba.convert("RGB")
    blended = _blend_rgb(dst_rgb, src_rgb, mode)
    # A transparent destination has no underlying colour: use the source colour there.
    blended = Image.composite(blended, src_rgb, dst_rgba.getchannel("A"))
    src_alpha = src_rgba.getchannel("A")
    # Preserve source RGB where the destination has no visible pixel.
    mix_mask = ImageChops.lighter(src_alpha, ImageChops.invert(dst_rgba.getchannel("A")))
    mixed_rgb = Image.composite(blended, dst_rgb, mix_mask)
    result = Image.alpha_composite(dst_rgba, src_rgba)
    result.paste(mixed_rgb, (0, 0))
    destination.paste(result)
