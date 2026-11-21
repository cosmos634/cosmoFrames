# CosmoFrames promo video

A 30-second vertical promotional project built only with the lightweight Pillow renderer features supported by CosmoFrames V1.1.

## Render on Termux

From the repository root:

```sh
node dist/cli.js validate examples/cosmoframes-ad/project.json
node dist/cli.js preview examples/cosmoframes-ad/project.json --time 2
node dist/cli.js render examples/cosmoframes-ad/project.json
```

Output: `examples/cosmoframes-ad/cosmoframes-ad.mp4`

## Format
- 480 × 854 vertical, 24 FPS, 30 seconds
- Animated typography, geometric accents, gradients, fades and keyframes
- No external image, font, browser, plugin or AI dependency
- No soundtrack is bundled; add a licensed instrumental track separately if desired

## Suggested sound
Use an original or properly licensed futuristic electronic instrumental: 100–115 BPM, restrained synth pulse, soft impacts on scene changes, and a short rising accent before the final logo. Keep the mix clean so the typography remains the focus.

## Accuracy
The video describes current repository features: CPU-first rendering, Termux/Linux workflow, keyframe animation, transitions and multi-track audio. It does not claim built-in AI video generation or GPU acceleration.
