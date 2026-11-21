# CosmoFrames Architecture

## Lightweight renderer

The default backend is Python/Pillow with CPU rendering and FFmpeg encoding. Modules under `python/cosmoframes/` divide responsibilities:

- `errors.py` — consistent CLI errors and exit codes
- `validation.py` — project structure, fields, colors, timing and animation validation
- `animation.py` — deterministic keyframe interpolation and easing
- `compositing.py` — alpha masks and CPU blend modes
- `transitions.py` — deterministic fade and directional wipe masks
- `plugins.py` — bounded loader for trusted Python frame-effect plugins
- `rendering.py` — Pillow drawing, scene composition and streamed FFmpeg export
- `profiling.py` — frame throughput and memory diagnostics
- `engine.py` — Python CLI entry point and project loading

The lightweight renderer processes one frame at a time. Its time convention is:

`time_seconds = frame_index / fps`

It never stores the complete video in RAM.

## Optional browser renderer

The browser backend lives in `src/browser.ts` and is invoked with `render-browser`. It attaches to an already-running Chromium instance over the DevTools Protocol through optional `playwright-core`. The project supplies `browser_entry`, an HTML file relative to the project JSON.

For each frame, the backend calls `window.cosmoframesRender(timeSeconds, frameIndex)` (or `window.renderAt`) when present, synchronizes Web Animations to the frame timestamp, captures one PNG screenshot, and streams it into FFmpeg. Browser-native HTML/CSS/JS, Canvas, SVG and JavaScript animation libraries can be used by the page. Browser rendering is a separate entry-page workflow; it does not reinterpret the lightweight scene element list.

The backend does not download or launch Chromium automatically. Keep the CDP endpoint bound to localhost because it grants control over the browser. The lightweight renderer never requires Chromium.

## Effect plugin API

The lightweight backend can load trusted Python effect modules listed in the project `plugins` array. A module exports `apply(image, time_seconds, settings)` and returns a Pillow image with unchanged dimensions. Plugin modules are cached in a bounded process-local cache. Loading a plugin executes Python code with the renderer's permissions, so projects must only reference trusted local files.

## Profiling

The `benchmark` CLI command measures sequential frame-render throughput, Python-tracked peak allocations, and process peak RSS where the platform exposes it. It does not encode video and is intended for comparing settings on the target device.

## Resource constraints

- Do not hold the complete video in RAM.
- Avoid unnecessary copies of full-resolution frames.
- Keep FFmpeg as a streaming encoder process.
- Keep image and gradient caches bounded.
- Respect the 8.3-megapixel frame limit to reduce out-of-memory failures on mobile.
- Keep browser dependencies out of the lightweight install path.
