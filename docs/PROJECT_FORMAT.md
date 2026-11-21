# CosmoFrames V1 Project Format

Project JSON uses version 1, resolution width and height, fps (default 30, maximum 60), duration seconds (default 5, maximum 600), background color, output filename, optional audio filename, and a non-empty scenes array. Media paths are relative to the project file.

Supported element types: text, rectangle, circle, polygon, image. Common fields include x, y, scale, opacity, rotation, start, end, color, and animations. Text supports text, fontSize, bold, and anchor. Rectangle supports width, height, radius. Circle supports radius. Polygon supports points as local [x,y] pairs. Image supports src, width, height.

Animations map a property name to keyframes: each keyframe has time, value, and optional easing. Easing values are linear, ease-in, ease-out, ease-in-out. Keyframe times must be strictly increasing and numeric values must be finite. Opacity values are in the 0–1 range; scale cannot be negative. Time is relative to the element start. Frame time is frame_index / fps. Colors must be valid Pillow/CSS-style color strings. Resolution dimensions are positive integers up to 8192; fps is 0.1–60 and duration is 0.01–600 seconds.

Current limitations: browser rendering (HTML/CSS/JS, Canvas, SVG, GSAP), masks, blend modes and advanced transition presets are not implemented. Unsupported element types fail validation.


## Scene timeline and transitions

Each scene may define `start` and `end` in project seconds. Defaults are 0 and the project duration. Scene elements use time relative to the scene start. Scenes are composited in array order.

A scene may define `transition_in`:

```json
"transition_in": { "type": "fade", "duration": 0.8 }
```

The currently supported transition is `fade`. Its duration is measured in seconds; it fades the scene from transparent to fully visible. Unsupported transition types are rejected instead of silently ignored.


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
