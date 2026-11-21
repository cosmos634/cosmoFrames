"""End-to-end test for multi-track audio MP4 export."""
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FFMPEG = shutil.which("ffmpeg")
if not FFMPEG:
    raise SystemExit("FFmpeg is required for this integration test.")

with tempfile.TemporaryDirectory(prefix="cosmoframes-audio-") as tmp:
    folder = Path(tmp)
    source = folder / "tone.wav"
    output = folder / "mixed.mp4"
    subprocess.run([FFMPEG, "-y", "-v", "error", "-f", "lavfi", "-i",
                    "sine=frequency=440:duration=1", "-c:a", "pcm_s16le", str(source)], check=True)
    project = {
        "version": 1, "resolution": {"width": 64, "height": 64},
        "fps": 12, "duration": 2, "output": str(output),
        "audio_tracks": [
            {"src": str(source), "start": 0, "volume": 0.3},
            {"src": str(source), "start": 0.4, "volume": 0.2}
        ],
        "scenes": [{"elements": [{"type": "rectangle", "x": 0, "y": 0,
                                  "width": 64, "height": 64, "color": "#ffffff"}]}]
    }
    project_path = folder / "project.json"
    project_path.write_text(json.dumps(project), encoding="utf-8")
    subprocess.run(["python", str(ROOT / "python" / "engine.py"), "render",
                    str(project_path)], check=True)
    if not output.is_file() or output.stat().st_size == 0:
        raise SystemExit("Audio integration test did not produce an MP4.")
    probe = subprocess.run([FFMPEG, "-v", "error", "-i", str(output),
                            "-map", "0:a:0", "-f", "null", "-"],
                           capture_output=True, text=True)
    if probe.returncode:
        raise SystemExit("Output MP4 audio stream is invalid: " + probe.stderr)
    print("Multi-track audio render integration test passed.")
