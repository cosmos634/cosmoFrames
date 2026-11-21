# CosmoFrames V1 Project Format

Project JSON uses version 1, resolution width and height, fps (default 30, maximum 60), duration seconds (default 5, maximum 600), background color, output filename, optional audio filename, and a non-empty scenes array. Media paths are relative to the project file.

Supported element types: text, rectangle, circle, polygon, image. Common fields include x, y, scale, opacity, rotation, start, end, color, and animations. Text supports text, fontSize, bold, and anchor. Rectangle supports width, height, radius. Circle supports radius. Polygon supports points as local [x,y] pairs. Image supports src, width, height.

Animations map a property name to keyframes: each keyframe has time, value, and optional easing. Easing values are linear, ease-in, ease-out, ease-in-out. Time is relative to the element start. Frame time is frame_index / fps.

Current limitations: gradients, transitions, multiple audio tracks, HTML/CSS/JS, Canvas, SVG, and GSAP are not implemented in V1. Unsupported element types fail validation.
