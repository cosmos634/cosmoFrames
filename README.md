# CosmoFrames

A lightweight, CPU-first video rendering engine for Android Termux and Linux.

## V1 status

The repository currently contains the first working-code foundation:
- TypeScript CLI commands: info, init, validate, preview, render
- Modular Python package: validation, keyframe animation, Pillow drawing, FFmpeg export and CLI entry point
- Python/Pillow frame renderer for text, rectangles, circles, polygons and images
- Deterministic keyframe interpolation with linear, ease-in, ease-out and ease-in-out easing
- Frame-by-frame RGB streaming into FFmpeg (no full-video frame buffer)
- MP4 H.264 output and optional single audio input muxed as AAC
- 480p vertical example project
- Claude Code skill and project-format documentation

Not implemented yet: Chromium/CDP browser rendering, HTML/CSS/JS execution, Canvas/SVG, gradients, transition presets, multi-track audio, caching and profiling. These are not advertised as working V1 features yet. The browser backend is optional and is not needed by the current renderer.

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
```

The rendered file is written to examples/vertical-demo/cosmoframes-demo.mp4.

To create a new project:

```sh
node dist/cli.js init my-video
node dist/cli.js validate my-video/project.json
node dist/cli.js render my-video/project.json
```

## Audio

Add an audio path to the project root, relative to project.json:

```json
"audio": "music.mp3"
```

FFmpeg muxes the audio as AAC. The current implementation supports one audio file.

## Development

```sh
npm test
python -m unittest discover -s tests -p 'test_*.py'
```

Always verify actual output on the target device. Android codec availability and performance vary by FFmpeg build.
