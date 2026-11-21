import importlib.util
import tempfile
import unittest
from PIL import Image
from pathlib import Path
import sys

PYTHON_DIR = Path(__file__).resolve().parents[1] / "python"
sys.path.insert(0, str(PYTHON_DIR))
from cosmoframes.compositing import composite
from cosmoframes.plugins import apply_plugins

ENGINE = PYTHON_DIR / "engine.py"
spec = importlib.util.spec_from_file_location("cosmoframes_engine", ENGINE)
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)

class EngineTests(unittest.TestCase):
    def test_keyframe_interpolation(self):
        el = {"animations": {"x": [{"time": 0, "value": 0}, {"time": 2, "value": 20}]}}
        self.assertEqual(engine.value(el, "x", 99, 1), 10)

    def test_ease_out(self):
        self.assertAlmostEqual(engine.ease("ease-out", 0.5), 0.75)

    def test_rejects_unknown_element(self):
        with self.assertRaises(SystemExit):
            engine.validate({"version": 1, "resolution": {"width": 10, "height": 10}, "scenes": [{"elements": [{"type": "video"}]}]})

    def test_rejects_duplicate_keyframe_times(self):
        project = {"version": 1, "resolution": {"width": 10, "height": 10}, "scenes": [{"elements": [{"type": "circle", "animations": {"x": [{"time": 0, "value": 0}, {"time": 0, "value": 5}]}}]}]}
        with self.assertRaises(SystemExit):
            engine.validate(project)

    def test_rejects_invalid_easing(self):
        project = {"version": 1, "resolution": {"width": 10, "height": 10}, "scenes": [{"elements": [{"type": "circle", "animations": {"x": [{"time": 0, "value": 0, "easing": "bounce"}]}}]}]}
        with self.assertRaises(SystemExit):
            engine.validate(project)

    def test_accepts_valid_animation_project(self):
        project = {"version": 1, "resolution": {"width": 64, "height": 64}, "fps": 24, "duration": 2, "scenes": [{"elements": [{"type": "circle", "x": 5, "y": 5, "radius": 4, "animations": {"x": [{"time": 0, "value": 5}, {"time": 1, "value": 20, "easing": "ease-out"}]}}]}]}
        engine.validate(project)
    def test_rejects_invalid_color(self):
        project = {"version": 1, "resolution": {"width": 10, "height": 10}, "background": "not-a-color", "scenes": [{"elements": []}]}
        with self.assertRaises(SystemExit):
            engine.validate(project)

    def test_rejects_opacity_outside_unit_interval(self):
        project = {"version": 1, "resolution": {"width": 10, "height": 10}, "scenes": [{"elements": [{"type": "circle", "animations": {"opacity": [{"time": 0, "value": 2}]}}]}]}
        with self.assertRaises(SystemExit):
            engine.validate(project)
    def test_rejects_negative_element_end(self):
        project = {"version": 1, "resolution": {"width": 10, "height": 10}, "scenes": [{"elements": [{"type": "circle", "end": -1}]}]}
        with self.assertRaises(SystemExit):
            engine.validate(project)
    def test_scene_fade_transition_blends_from_background(self):
        p = {"resolution": {"width": 64, "height": 64}, "fps": 24, "duration": 2,
             "background": "#000000", "scenes": [{"transition_in": {"type": "fade", "duration": 1},
             "elements": [{"type": "rectangle", "x": 0, "y": 0, "width": 64, "height": 64, "color": "#ffffff"}]}],
             "_base": Path(".")}
        image = engine.frame(p, 12)
        pixel = image.getpixel((32, 32))
        self.assertTrue(115 <= pixel[0] <= 140, pixel)

    def test_scene_wipe_left_transition(self):
        p = {"resolution": {"width": 64, "height": 32}, "fps": 24, "duration": 2,
             "background": "#000000", "scenes": [{"transition_in": {"type": "wipe_left", "duration": 1},
             "elements": [{"type": "rectangle", "x": 0, "y": 0, "width": 64, "height": 32, "color": "#ffffff"}]}],
             "_base": Path(".")}
        image = engine.frame(p, 12)
        self.assertEqual(image.getpixel((8, 16)), (255, 255, 255))
        self.assertEqual(image.getpixel((56, 16)), (0, 0, 0))

    def test_scene_fade_out_transition(self):
        p = {"resolution": {"width": 32, "height": 32}, "fps": 10, "duration": 2,
             "background": "#000000", "scenes": [{"transition_out": {"type": "fade", "duration": 1},
             "elements": [{"type": "rectangle", "x": 0, "y": 0, "width": 32, "height": 32, "color": "#ffffff"}]}],
             "_base": Path(".")}
        image = engine.frame(p, 15)
        value = image.getpixel((16, 16))[0]
        self.assertTrue(115 <= value <= 140, value)

    def test_rejects_transition_longer_than_scene(self):
        project = {"version": 1, "resolution": {"width": 10, "height": 10}, "duration": 2,
                   "scenes": [{"end": 1, "transition_in": {"type": "fade", "duration": 1.5}, "elements": []}]}
        with self.assertRaises(SystemExit):
            engine.validate(project)

    def test_scene_start_and_end_boundaries(self):
        p = {"resolution": {"width": 64, "height": 64}, "fps": 24, "duration": 3,
             "background": "#000000", "scenes": [{"start": 1, "end": 2,
             "elements": [{"type": "rectangle", "x": 0, "y": 0, "width": 64, "height": 64, "color": "#ffffff"}]}],
             "_base": Path(".")}
        self.assertEqual(engine.frame(p, 0).getpixel((32, 32)), (0, 0, 0))
        self.assertEqual(engine.frame(p, 48).getpixel((32, 32)), (0, 0, 0))
        self.assertEqual(engine.frame(p, 24).getpixel((32, 32)), (255, 255, 255))

    def test_validates_audio_tracks(self):
        project = {"version": 1, "resolution": {"width": 10, "height": 10},
                   "audio_tracks": [{"src": "music.wav", "start": 0.25, "volume": 0.7}],
                   "scenes": [{"elements": []}]}
        engine.validate(project)

    def test_rejects_audio_track_volume_above_limit(self):
        project = {"version": 1, "resolution": {"width": 10, "height": 10},
                   "audio_tracks": [{"src": "music.wav", "volume": 5}],
                   "scenes": [{"elements": []}]}
        with self.assertRaises(SystemExit):
            engine.validate(project)

    def test_rejects_unsupported_scene_transition(self):
        project = {"version": 1, "resolution": {"width": 10, "height": 10},
                   "scenes": [{"transition_in": {"type": "wipe", "duration": 1}, "elements": []}]}
        with self.assertRaises(SystemExit):
            engine.validate(project)

    def test_element_gradient_fill(self):
        p = {"resolution": {"width": 64, "height": 32}, "fps": 24, "duration": 1,
             "background": "#000000", "scenes": [{"elements": [
                 {"type": "rectangle", "x": 0, "y": 0, "width": 64, "height": 32,
                  "gradient": {"type": "linear", "colors": ["#ff0000", "#0000ff"]}}
             ]}], "_base": Path(".")}
        image = engine.frame(p, 0)
        left = image.getpixel((3, 16))
        right = image.getpixel((60, 16))
        self.assertGreater(left[0], left[2])
        self.assertGreater(right[2], right[0])

    def test_background_gradient(self):
        p = {"resolution": {"width": 64, "height": 32}, "fps": 24, "duration": 1,
             "background_gradient": {"type": "linear", "colors": ["#000000", "#ffffff"]},
             "scenes": [{"elements": []}], "_base": Path(".")}
        image = engine.frame(p, 0)
        self.assertNotEqual(image.getpixel((0, 10)), image.getpixel((63, 10)))

    def test_validates_animated_font_size(self):
        project = {"version": 1, "resolution": {"width": 64, "height": 64}, "scenes": [
            {"elements": [{"type": "text", "text": "Hi", "fontSize": 12,
             "animations": {"fontSize": [{"time": 0, "value": 12}, {"time": 1, "value": 30}]}}]}]}
        engine.validate(project)

    def test_alpha_mask_hides_part_of_layer(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            mask = Image.new("L", (64, 32), 0)
            for x in range(32, 64):
                for y in range(32):
                    mask.putpixel((x, y), 255)
            mask.save(base / "mask.png")
            p = {"resolution": {"width": 64, "height": 32}, "fps": 24, "duration": 1,
                 "background": "#000000", "scenes": [{"elements": [
                     {"type": "rectangle", "x": 0, "y": 0, "width": 64, "height": 32,
                      "color": "#ffffff", "mask": {"src": "mask.png"}}
                 ]}], "_base": base}
            image = engine.frame(p, 0)
            self.assertEqual(image.getpixel((10, 16)), (0, 0, 0))
            self.assertEqual(image.getpixel((50, 16)), (255, 255, 255))

    def test_multiply_blend_mode(self):
        destination = Image.new("RGBA", (2, 2), (128, 128, 128, 255))
        source = Image.new("RGBA", (2, 2), (128, 0, 255, 255))
        composite(destination, source, "multiply")
        pixel = destination.getpixel((0, 0))
        self.assertTrue(63 <= pixel[0] <= 65, pixel)
        self.assertEqual(pixel[1], 0)
        self.assertEqual(pixel[2], 128)

    def test_rejects_unknown_blend_mode(self):
        project = {"version": 1, "resolution": {"width": 10, "height": 10},
                   "scenes": [{"elements": [{"type": "circle", "blend_mode": "burn"}]}]}
        with self.assertRaises(SystemExit):
            engine.validate(project)

    def test_all_blend_mode_formulas(self):
        destination = Image.new("RGBA", (1, 1), (128, 128, 128, 255))
        expected = {"multiply": 64, "screen": 192, "add": 255, "overlay": 129}
        for mode, channel in expected.items():
            result = destination.copy()
            composite(result, Image.new("RGBA", (1, 1), (128, 128, 128, 255)), mode)
            self.assertAlmostEqual(result.getpixel((0, 0))[0], channel, delta=1, msg=mode)

    def test_blend_modes_handle_transparent_source_pixels(self):
        for mode in ("multiply", "screen", "add", "overlay"):
            destination = Image.new("RGBA", (1, 1), (40, 80, 120, 255))
            source = Image.new("RGBA", (1, 1), (255, 255, 255, 0))
            composite(destination, source, mode)
            self.assertEqual(destination.getpixel((0, 0)), (40, 80, 120, 255))

    def test_blend_mode_preserves_alpha_on_empty_destination(self):
        destination = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
        source = Image.new("RGBA", (1, 1), (200, 100, 50, 128))
        composite(destination, source, "screen")
        self.assertEqual(destination.getpixel((0, 0)), (200, 100, 50, 128))

    def test_rejects_resolution_over_mobile_pixel_limit(self):
        project = {"version": 1, "resolution": {"width": 4096, "height": 2160},
                   "scenes": [{"elements": []}]}
        with self.assertRaises(SystemExit):
            engine.validate(project)

    def test_rejects_negative_animated_font_size(self):
        project = {"version": 1, "resolution": {"width": 10, "height": 10},
                   "scenes": [{"elements": [{"type": "text", "text": "x",
                   "animations": {"fontSize": [{"time": 0, "value": -2}]}}]}]}
        with self.assertRaises(SystemExit):
            engine.validate(project)

    def test_python_effect_plugin_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            plugin = base / "effect.py"
            plugin.write_text(
                "from PIL import Image\ndef apply(image, time_seconds, settings):\n"
                "    return Image.new('RGBA', image.size, (int(time_seconds * 10), 20, 30, 255))\n",
                encoding="utf-8")
            source = Image.new("RGBA", (4, 4), (0, 0, 0, 255))
            output = apply_plugins(source, [{"src": "effect.py", "settings": {}}], base, 2.5)
            self.assertEqual(output.getpixel((0, 0)), (25, 20, 30, 255))

    def test_rejects_invalid_mask_config(self):
        project = {"version": 1, "resolution": {"width": 10, "height": 10},
                   "scenes": [{"elements": [{"type": "circle", "mask": {"src": ""}}]}]}
        with self.assertRaises(SystemExit):
            engine.validate(project)

    def test_renders_rgb_frame(self):
        p = {"resolution": {"width": 64, "height": 64}, "fps": 24, "duration": 1,
             "background": "#000000", "scenes": [{"elements": [{"type": "circle", "x": 32, "y": 32, "radius": 10, "color": "#ffffff"}]}],
             "_base": Path(".")}
        image = engine.frame(p, 0)
        self.assertEqual(image.mode, "RGB")
        self.assertEqual(image.size, (64, 64))

if __name__ == "__main__":
    unittest.main()
