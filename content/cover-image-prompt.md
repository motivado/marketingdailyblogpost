# TokyLabs Blog Cover — Image Generation Recipe

**This is the saved, approved recipe for every blog cover image.**
Model: **Nano Banana Pro** (Google Gemini) — model id `gemini-3-pro-image`.
Auth: `GEMINI_API_KEY` (environment secret; never in repo/logs/commits).
API: `POST https://generativelanguage.googleapis.com/v1beta/models/gemini-3-pro-image:generateContent?key=$GEMINI_API_KEY`
Config: `generationConfig.responseModalities:["IMAGE"]`, `imageConfig.aspectRatio:"16:9"`.
Output is JPEG — save covers as `.jpg`.

## Style prompt (fill the three {BRACKETS} per article)

```
Minimalist single-continuous-line art doodle, hand-drawn, on a plain textured
off-white paper background. Subject: {SUBJECT}.

CRITICAL STYLE: each character and object is drawn with a SINGLE continuous fluid
line in deep indigo (#30197C) — one unbroken, confident, gestural stroke per
figure, like a quick one-line contour sketch done without lifting the pen. Use
the absolute minimum number of strokes to define each form, essential lines only.
Leave vast empty white space around everything. Raw, quick, conceptual, loose and
imperfect — like a designer doodle, NOT a polished vector illustration, NOT a
cartoon with filled shapes.

Zero rendering: no shading, no hatching, no gradients, no fill on the figures —
they are pure outline only.

ONE single accent: {ACCENT} is filled with a textured magenta (#ff0082)
crayon-like block of color, rough and uneven like a wax crayon scribble. This is
the only filled color area in the whole image.

A final single broad horizontal cyan (#41C5EE) brush stroke sits beneath the
figures to suggest {GROUND}, painted with extreme economy in one gesture.

Flat, no perspective, no furniture, no background objects, no patterns. No text,
no words, no letters, no numbers, no logos anywhere. 16:9 landscape, lots of
negative space.
```

## Variable guidance

- `{SUBJECT}` — the article's action/scene: who is doing what (a child, a parent
  and child, a teacher and students, an educator presenting). Keep it to one
  clear action with 1–3 figures plus one relevant object.
- `{ACCENT}` — the single most meaningful object, filled magenta. Exactly one.
- `{GROUND}` — what the cyan stroke implies: floor line, table surface, horizon.

## Palette roles (do not deviate)

| Color   | Hex       | Role in the image                                  |
|---------|-----------|----------------------------------------------------|
| Indigo  | `#30197C` | All contour linework (dominant)                    |
| Cyan    | `#41C5EE` | The single ground/environment brush stroke         |
| Magenta | `#ff0082` | The one crayon-textured accent fill                |
| Amber   | `#ffd200` | RESERVED for critical alerts — never in cover art  |

## Hard rules

- Exactly ONE magenta fill. No second filled area.
- No shading, gradients, or background detail. Vast empty space.
- No text, letters, numbers, or logos in the image.
- Never use amber in covers.

## Reference examples (generated 2026-07-17, approved)

| Article | {SUBJECT} | {ACCENT} | {GROUND} |
|---|---|---|---|
| NASA robot swarms | child crouching to watch a swarm of tiny wheeled robots explore | one swarm robot | classroom floor |
| Mini catapult | parent + child firing a small desktop catapult, ball arcing | the flying ball | table surface |
| ESA robotics | teacher kneeling with a child, watching a small rover | the rover body | classroom floor |
| DIY water dispenser | two kids building a bottle water dispenser dripping into a cup | the bottle | table surface |
| Education conferences | educator presenting a robot on a stand to two listeners | the robot on the stand | conference-hall floor |
