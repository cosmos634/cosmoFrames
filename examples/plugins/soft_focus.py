"""Example optional effect plugin: subtle soft-focus blend."""
from PIL import Image, ImageFilter


def apply(image, time_seconds, settings):
    radius = max(0.0, min(12.0, float(settings.get("radius", 2.0))))
    amount = max(0.0, min(1.0, float(settings.get("amount", 0.12))))
    if radius == 0 or amount == 0:
        return image
    blurred = image.filter(ImageFilter.GaussianBlur(radius))
    return Image.blend(image.convert("RGBA"), blurred.convert("RGBA"), amount)
