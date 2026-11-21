# CosmoFrames

A lightweight, CPU-first video rendering engine for Android Termux and Linux.

## V1.1 status

The repository currently contains the first working-code foundation:
- TypeScript CLI commands: info, init, validate, preview, render, render-browser, benchmark
- Modular Python package: validation, animation, compositing, transitions, trusted effect plugins, profiling and FFmpeg export
- Python/Pillow frame renderer for text, rectangles, circles, polygons and images
- Deterministic keyframe interpolation with linear, ease-in, ease-out and ease-in-out easing
- Frame-by-frame RGB streaming into FFmpeg (no full-video frame buffer)
- MP4 H.264 output with single or multi-track AAC audio
- 480p vertical example project
- Claude Code skill and project-format documentation

Implemented: fade and directional wipe scene transitions (in/out), linear gradients, animated text/image dimensions, multi-track audio, bounded asset caches, alpha masks, and CPU blend modes (multiply, screen, add, overlay).

The optional Chromium/CDP backend is available through `render-browser`. It renders an HTML entry page using a deterministic `window.cosmoframesRender(timeSeconds, frameIndex)` hook and streams PNG frames into FFmpeg. It supports browser-native HTML/CSS/JS, Canvas, SVG and libraries such as GSAP when those are included by the page. Vector-path masks and GPU acceleration are not implemented.

See [Architecture](docs/ARCHITECTURE.md), [Project Format](docs/PROJECT_FORMAT.md) and [Changelog](CHANGELOG.md) for implementation details.

## Requirements

- Node.js 20+ recommended
- Python 3.10+
- Pillow
- FFmpeg with libx264 encoder
- Chromium is not required

## Install on Termux

```sh
pkg update
pkg install nodejs python ffmpeg
git clone https://github.com/cosmos634/cosmoFrames.git
cd cosmoFrames
npm install
npm run build
python -m pip install -r python/requirements.txt
```

## Run

```sh
node dist/cli.js info
node dist/cli.js validate examples/vertical-demo/project.json
node dist/cli.js preview examples/vertical-demo/project.json --time 1.5
node dist/cli.js render examples/vertical-demo/project.json
node dist/cli.js benchmark examples/vertical-demo/project.json --frames 24
```

The rendered file is written to examples/vertical-demo/cosmoframes-demo.mp4.

Frame dimensions are capped at 8.3 megapixels per project to reduce out-of-memory failures on phones. Asset, font and gradient caches are bounded and kept intentionally small.

To create a new project:

```sh
node dist/cli.js init my-video
node dist/cli.js validate my-video/project.json
node dist/cli.js render my-video/project.json
```

## Python effect plugins

A project may list trusted Python effects in its `plugins` array. Each plugin is a local Python file that exports `apply(image, time_seconds, settings)` and returns a Pillow image with unchanged dimensions.

```json
"plugins": [
  { "src": "../plugins/soft_focus.py", "settings": { "radius": 2, "amount": 0.12 } }
]
```

See [plugin demo](examples/plugin-demo/project.json). **Only load plugins you trust:** Python plugins execute code with the same permissions as the renderer.

## Optional browser renderer

Install the optional Node dependency and start a local Chromium instance with the DevTools Protocol enabled:

```sh
npm install playwright-core
chromium --headless=new --remote-debugging-port=9222 --user-data-dir=/tmp/cosmoframes-chrome
node dist/cli.js render-browser examples/browser-demo/project.json
```

Keep the CDP port bound to localhost; it grants control over the browser. Set `COSMOFRAMES_CDP_URL` if Chromium listens on another local endpoint. Browser rendering is optional and does not affect the Pillow renderer or its install path. See [browser demo](examples/browser-demo/project.json).

## Profiling

Use `benchmark` to measure frame-render speed and memory on the current device. It renders frames without encoding an MP4; by default it benchmarks up to 120 frames.

```sh
node dist/cli.js benchmark project.json --frames 120
```

## Audio

Add an audio path to the project root, relative to project.json:

```json
"audio_tracks": [
  { "src": "music.mp3", "start": 0, "volume": 0.35 },
  { "src": "voice.wav", "start": 1.2, "volume": 1.0 }
]
```

FFmpeg mixes all tracks and muxes the result as AAC. The legacy `audio` field remains supported.

## Development

```sh
npm test
python -m unittest discover -s tests -p 'test_*.py'
```

Always verify actual output on the target device. Android codec availability and performance vary by FFmpeg build.
