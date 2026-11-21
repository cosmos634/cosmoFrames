# CosmoFrames Development Skill

## Architecture
V1 is a Termux-first Python/Pillow CPU renderer. TypeScript CLI delegates to Python. Python evaluates deterministic frame times, draws one frame at a time, and streams RGB bytes to FFmpeg. Chromium is optional and is not required for V1.

## Rules
- Keep modules independent and avoid native Node dependencies.
- Never buffer a full video in RAM.
- Frame time is frame_index divided by fps.
- Fail clearly for unsupported elements; never silently skip effects.
- Do not require GPU, Chromium, cloud, Docker, Electron, or AI APIs.
- Never overwrite user files during init.
- Resolve media paths relative to the project JSON.
- Validate untrusted JSON before rendering.

## Project format
Root: version 1, resolution width/height, fps, duration, background, output, optional audio, non-empty scenes. Scene: elements array. V1 elements: text, rectangle, circle, polygon, image. Keyframes live in animations.property arrays and contain time, value, optional easing.

## Tests and workflow
Run npm install, npm run build, python -m pip install -r python/requirements.txt, then validate and render examples/vertical-demo/project.json. Inspect the resulting MP4 with ffprobe. Add regression tests for schema, interpolation, drawing, and FFmpeg failures.

Do not claim browser support until a real Chromium/CDP implementation has passed tests on the target device. Keep V2 browser features out of V1.
