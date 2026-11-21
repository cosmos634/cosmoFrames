# CosmoFrames Development Skill

## Architecture
CosmoFrames 1.1 is a Termux-first video engine with two independent backends:
- Lightweight: Python/Pillow CPU rendering, one frame at a time, streamed to FFmpeg.
- Optional browser: TypeScript + playwright-core, attaches to an already-running Chromium through CDP and streams PNG screenshots to FFmpeg.

The lightweight backend is the default. Chromium is never required for normal install, validation, preview or rendering.

## Rules
- Never buffer a full video in RAM.
- Frame time is deterministic: frame_index / fps.
- Resolve all media and plugin paths relative to the project JSON.
- Validate project JSON before lightweight rendering.
- Fail clearly for unsupported effects; never silently skip them.
- Keep caches bounded and respect the 8.3-megapixel frame safety limit.
- Do not require GPU, Docker, Electron, cloud services or AI APIs.
- Never overwrite user files during init.
- Python plugins execute arbitrary code; only load trusted local plugins.
- Keep Chromium/CDP bound to localhost; a CDP endpoint grants browser control.
- Browser pages may define window.cosmoframesRender(timeSeconds, frameIndex) for deterministic per-frame updates.

## Lightweight project format
Root: version 1, resolution, fps, duration, background, output, optional audio/audio_tracks, plugins, and non-empty scenes. Scene: start/end, transition_in/transition_out, blend_mode and elements. Elements: text, rectangle, circle, polygon and image. Keyframes are numeric and deterministic; easing: linear, ease-in, ease-out, ease-in-out.

## Tests and workflow
Run npm install, npm run build, python -m pip install -r python/requirements.txt, npm test, validate all examples, preview the plugin demo, render the vertical demo, run the multi-track audio integration test and benchmark. CI performs these checks on Linux. The optional browser backend requires a local Chromium/CDP runtime and must also be tested on the target environment before claiming Android browser compatibility.

Do not add Chromium to the lightweight dependency path. Keep the browser renderer optional.
