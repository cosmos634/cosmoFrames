# CosmoFrames V1 Project Format

Project JSON uses version 1, resolution width and height, fps (default 30, maximum 60), duration seconds (default 5, maximum 600), background color, output filename, optional audio filename, and a non-empty scenes array. Media paths are relative to the project file.

Supported element types: text, rectangle, circle, polygon, image. Common fields include x, y, scale, opacity, rotation, start, end, color, and animations. Text supports text, fontSize, bold, and anchor. Rectangle supports width, height, radius. Circle supports radius. Polygon supports points as local [x,y] pairs. Image supports src, width, height.

Animations map a property name to keyframes: each keyframe has time, value, and optional easing. Easing values are linear, ease-in, ease-out, ease-in-out. Keyframe times must be strictly increasing and numeric values must be finite. Opacity values are in the 0–1 range; scale cannot be negative. Time is relative to the element start. Frame time is frame_index / fps. Colors must be valid Pillow/CSS-style color strings. Resolution dimensions are positive integers up to 8192; fps is 0.1–60 and duration is 0.01–600 seconds.

Current limitations: gradients, transitions, multiple audio tracks, HTML/CSS/JS, Canvas, SVG, and GSAP are not implemented in V1. Unsupported element types fail validation.
