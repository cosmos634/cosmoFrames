# CosmoFrames V1 Project Format

Project JSON uses version 1, resolution width and height, fps (default 30, maximum 60), duration seconds (default 5, maximum 600), background color, output filename, optional audio filename, and a non-empty scenes array. Media paths are relative to the project file.

Supported element types: text, rectangle, circle, polygon, image. Common fields include x, y, scale, opacity, rotation, start, end, color, and animations. Text supports text, fontSize, bold, and anchor. Rectangle supports width, height, radius. Circle supports radius. Polygon supports points as local [x,y] pairs. Image supports src, width, height.

Animations map a property name to keyframes: each keyframe has time, value, and optional easing. Easing values are linear, ease-in, ease-out, ease-in-out. Keyframe times must be strictly increasing and numeric values must be finite. Opacity values are in the 0–1 range; scale cannot be negative. Time is relative to the element start. Frame time is frame_index / fps. Colors must be valid Pillow/CSS-style color strings. Resolution dimensions are positive integers up to 8192 per side, with a total limit of 8.3 megapixels to protect memory on mobile devices; fps is 0.1–60 and duration is 0.01–600 seconds.

Current limitations: browser rendering (HTML/CSS/JS, Canvas, SVG, GSAP), vector-path masks, and advanced transition presets are not implemented. Unsupported element types fail validation.


## Scene timeline and transitions

Each scene may define `start` and `end` in project seconds. Defaults are 0 and the project duration. Scene elements use time relative to the scene start. Scenes are composited in array order.

Scenes may define `transition_in` and `transition_out`:

```json
"transition_in": { "type": "wipe_left", "duration": 0.8 },
"transition_out": { "type": "fade", "duration": 0.5 }
```

Supported types: `fade`, `wipe_left`, `wipe_right`, `wipe_up`, and `wipe_down`. Durations are in seconds and cannot exceed the scene duration. Wipes reveal or hide the scene from the named edge. Transitions are deterministic and CPU-rendered. Unsupported types are rejected.


## Audio tracks

The legacy `audio` field remains supported for one audio file. For multiple tracks, use `audio_tracks`:

```json
"audio_tracks": [
  { "src": "music.wav", "start": 0, "volume": 0.35 },
  { "src": "voice.wav", "start": 1.2, "volume": 1.0 }
]
```

Each track is mixed into the MP4 audio stream. `start` is its offset in project seconds and `volume` is a multiplier from 0 to 4. Audio paths are resolved relative to the project JSON file. If both `audio` and `audio_tracks` are present, the legacy audio file is mixed as an additional track.


## Gradients

A linear gradient can be used as the project background or as a fill for text and vector shapes:

```json
"background_gradient": {
  "type": "linear",
  "colors": ["#101018", "#202060", "#20d9e8"],
  "angle": 0
}
```

For an element, place the same object in its `gradient` field. Two to eight valid colors are supported. The angle is in degrees. Image elements use their source image rather than a gradient fill.

Text `fontSize`, image `width` and image `height` can be animated with numeric keyframes.


## Masks and blend modes

An element can use a grayscale image as an alpha mask. White keeps the layer visible, black hides it, and gray values create partial transparency:

```json
"mask": { "src": "masks/title-mask.png", "invert": false }
```

The mask is resized to the project frame dimensions. Set `invert` to `true` to reverse it. Mask image paths are relative to the project JSON file.

Elements and scenes support `blend_mode`: `normal`, `multiply`, `screen`, `add`, and `overlay`. The default is `normal`. These modes are composited on the CPU; complex projects may render more slowly on low-end phones.
