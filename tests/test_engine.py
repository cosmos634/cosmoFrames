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

    def test_renders_rgb_frame(self):
        p = {"resolution": {"width": 64, "height": 64}, "fps": 24, "duration": 1,
             "background": "#000000", "scenes": [{"elements": [{"type": "circle", "x": 32, "y": 32, "radius": 10, "color": "#ffffff"}]}],
             "_base": Path(".")}
        image = engine.frame(p, 0)
        self.assertEqual(image.mode, "RGB")
        self.assertEqual(image.size, (64, 64))

if __name__ == "__main__":
    unittest.main()
