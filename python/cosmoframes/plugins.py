"""Trusted user plugin loader for per-frame image effects."""
import importlib.util
import sys
from functools import lru_cache
from pathlib import Path
from PIL import Image


@lru_cache(maxsize=8)
def _load(path):
    source = Path(path)
    if not source.is_file():
        raise ValueError("Plugin file not found: " + str(source))
    spec = importlib.util.spec_from_file_location("cosmoframes_plugin_" + str(abs(hash(str(source)))), source)
    if spec is None or spec.loader is None:
        raise ValueError("Could not load plugin: " + str(source))
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(spec.name, None)
        raise
    apply = getattr(module, "apply", None)
    if not callable(apply):
        raise ValueError("Plugin must define apply(image, time_seconds, settings).")
    return apply


def apply_plugins(image, plugins, base, time_seconds):
    result = image
    for item in plugins:
        path = (base / item["src"]).resolve()
        apply = _load(str(path))
        output = apply(result, time_seconds, item.get("settings", {}))
        if not isinstance(output, Image.Image):
            raise ValueError("Plugin must return a Pillow Image.")
        if output.size != result.size:
            raise ValueError("Plugin must preserve the frame dimensions.")
        if output.mode not in ("RGB", "RGBA"):
            output = output.convert("RGBA")
        result = output
    return result
