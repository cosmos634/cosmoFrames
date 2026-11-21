# CosmoFrames Architecture

## Current lightweight backend

The current renderer is split into small Python modules under `python/cosmoframes/`:

- `errors.py` — consistent CLI errors and exit codes
- `validation.py` — project schema, asset fields, colors and animation validation
- `animation.py` — deterministic keyframe interpolation and easing
- `rendering.py` — Pillow drawing, frame composition and FFmpeg streaming
- `engine.py` — command-line entry point and project loading

The lightweight backend is the default and only implemented backend in the current release. It renders one frame at a time and streams raw RGB bytes to FFmpeg.

## Backend boundary

A future browser backend must consume the same project timeline and frame-time convention:

`time_seconds = frame_index / fps`

It must remain optional. Installing or using the lightweight backend must never require Chromium, a GPU, Docker, or a cloud service.

## Planned browser backend

The planned browser backend may use HTML/CSS/JS, Canvas or SVG, with Chromium controlled through CDP where supported. It is not implemented yet and must not be treated as available functionality.

## Profiling

The `benchmark` CLI command measures sequential frame-render throughput, Python-tracked peak allocations, and process peak RSS where the platform exposes it. It does not encode video and is intended for comparing settings on the target device.

## Resource constraints

- Do not hold the complete video in RAM.
- Avoid unnecessary copies of full-resolution frames.
- Keep FFmpeg as a streaming encoder process.
- Make temporary files explicit and clean them up.
- Keep browser dependencies out of the lightweight install path.


## Renderer caches

The lightweight renderer keeps bounded in-process caches for decoded source images, font objects and generated gradient surfaces. These caches avoid reopening and rebuilding identical assets on every frame. The caches are deliberately bounded to prevent unbounded memory growth on mobile devices; a new process starts with empty caches.
