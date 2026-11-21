# Changelog

## 1.1.0

- Added optional Chromium/CDP browser rendering for HTML/CSS/JavaScript pages, Canvas, SVG and browser-side animation libraries.
- Added deterministic browser frame hook: `window.cosmoframesRender(timeSeconds, frameIndex)`.
- Added trusted Python effect plugins with a stable Pillow image contract.
- Added fade and directional wipe scene transitions, including incoming and outgoing transitions.
- Added blend modes, alpha masks, gradients and multi-track audio support.
- Added frame-render benchmarking with Python allocation and process RSS diagnostics.
- Added a formal JSON Schema for version 1 projects and example projects for browser rendering and plugins.
- Reduced cache sizes and enforced an 8.3-megapixel frame safety limit for mobile devices.
- Expanded validation and CI coverage for rendering, transitions, plugins, browser project structure and audio muxing.

## 1.0.0

- Initial CPU-first Pillow renderer and TypeScript CLI.
- Frame-by-frame FFmpeg MP4 export.
- Keyframe animation, easing, image and vector drawing primitives.
