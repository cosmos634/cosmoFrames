"""Lightweight frame-render benchmark and memory diagnostics."""
import resource
import sys
import time
import tracemalloc

from .rendering import frame


def benchmark(project, frame_count=None):
    fps = float(project.get("fps", 30))
    total = max(1, int(float(project.get("duration", 5)) * fps))
    count = min(total, 120) if frame_count is None else min(total, frame_count)
    tracemalloc.start()
    started = time.perf_counter()
    for index in range(count):
        image = frame(project, index)
        image.close()
    elapsed = max(time.perf_counter() - started, 1e-9)
    _, peak_python = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    try:
        peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        peak_mb = peak_rss / (1024 * 1024 if sys.platform == "darwin" else 1024)
    except (AttributeError, OSError):
        peak_mb = None
    print("Benchmark: %d frames in %.2fs (%.2f FPS)" % (count, elapsed, count / elapsed))
    print("Python-tracked peak: %.1f MB" % (peak_python / (1024 * 1024)))
    if peak_mb is not None:
        print("Process peak RSS: %.1f MB" % peak_mb)
    print("Note: benchmark renders frames only; it does not encode MP4.")
