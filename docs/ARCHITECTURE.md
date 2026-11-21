# CosmoFrames Architecture

## Current lightweight backend

The current renderer is split into small Python modules under `python/cosmoframes/`:

- `errors.py` — consistent CLI errors and exit codes
- `validation.py` — project schema, asset fields, colors and animation validation
- `animation.py` — deterministic keyframe interpolation and easing
- `rendering.py` — Pillow drawing, frame composition and FFmpeg streaming
- `engine.py` — command-line entry point and project loading

The lightweight backend remains the default. The browser backend is optional and requires a separately installed Chromium instance with CDP enabled. It renders one frame at a time and streams raw RGB bytes to FFmpeg.

## Backend boundary

A future browser backend must consume the same project timeline and frame-time convention:

`time_seconds = frame_index / fps`

It must remain optional. Installing or using the lightweight backend must never require Chromium, a GPU, Docker, or a cloud service.

## Planned browser backend

The optional browser backend lives in `src/browser.ts`. It attaches to an already-running Chromium instance over CDP through the optional `playwright-core` package. A project supplies `browser_entry`, an HTML file relative to the project JSON. On each frame the renderer calls `window.cosmoframesRender(timeSeconds, frameIndex)` (or `window.renderAt`) when present, captures one PNG screenshot, and streams it into FFmpeg. This permits browser-native HTML/CSS/JS, Canvas, SVG and JS animation libraries while keeping Chromium out of the lightweight install path. The backend does not download or launch a browser automatically.

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
