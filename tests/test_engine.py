import importlib.util
import unittest
from pathlib import Path

ENGINE = Path(__file__).resolve().parents[1] / "python" / "engine.py"
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
    def test_renders_rgb_frame(self):
        p = {"resolution": {"width": 64, "height": 64}, "fps": 24, "duration": 1,
             "background": "#000000", "scenes": [{"elements": [{"type": "circle", "x": 32, "y": 32, "radius": 10, "color": "#ffffff"}]}],
             "_base": Path(".")}
        image = engine.frame(p, 0)
        self.assertEqual(image.mode, "RGB")
        self.assertEqual(image.size, (64, 64))

if __name__ == "__main__":
    unittest.main()
