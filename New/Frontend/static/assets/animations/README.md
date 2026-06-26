# Koa-AI Avatar Animations

The avatar plays **VRM animation clips** (`.vrma`). This folder holds:

- `converted_gltf/` — the `.vrma` clips actually played at runtime
- `raw_fbx/` — source `.fbx` files (clips are converted from these to `.vrma`)
- `index.md` — the registry that maps clips into named **categories**

## What ships today (only 2 clips / states)

| Category  | Clip         | When it plays                                          |
|-----------|--------------|--------------------------------------------------------|
| `neutral` | `Idle.vrma`  | at rest — on load, while listening/thinking, and after a reply |
| `taunt`   | `Taunt.vrma` | while the avatar is **speaking** (a gesture)           |

That's the whole library right now: **one idle pose and one gesture.** The
speaking gesture loops for the duration of a reply, then we return to idle.

The wiring lives in:
- [`app.js`](../../js/app.js) — calls `playAnimation('taunt')` when a reply starts
  and `playAnimation('neutral')` when the turn ends.
- [`scene.js`](../../js/modules/scene.js) — `playAnimation(category)` plays a random
  clip from a category; `updateVibe([x,y,z])` can pick a category from an emotion vector.

## `index.md` format

```
#<category>
- <File.vrma> <intensity>
```

A line starting with `#` begins a category; a line starting with `-` adds a clip
to it. Anything else (e.g. `//` lines) is ignored by the parser.

## How to add more animations

1. Put a new clip in `converted_gltf/` (convert an `.fbx` → `.vrma` if needed).
2. Register it in `index.md` under a new or existing category:
   ```
   #happy
   - Wave.vrma 1.0
   ```
3. Trigger it — two options:
   - **Directly:** call `playAnimation('happy')` from `app.js` at the right moment
     (e.g. on a new interaction state).
   - **By mood:** have the backend include an emotion / "vibe" value in the chat
     stream, then call `updateVibe([x, y, z])` so a category is chosen automatically.
     The backend currently sends **no** emotion signal, which is why gestures are
     tied to the speaking state for now.
