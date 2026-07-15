# Mono Line — Visual Style Guide

Generic style guideline for TokyLabs illustration/image generation (blog covers,
social posts, newsletters). Extracted from the minimalist line-art prompt
template; use it with any image generator (Canva, Midjourney, DALL-E, etc.).

## Core principles

1. **Line quality** — One continuous, fluid contour per subject. No redrawn
   edges, no corrections. The line is committed even when imperfect.
2. **Economy of mark** — Absolute minimum number of strokes. If a mark can be
   removed without losing meaning, remove it.
3. **Zero rendering** — No hatching, shading, gradients, or fills on subject
   forms. Visual weight comes from stroke alone.
4. **Negative space** — The majority of the frame stays empty. Whitespace is
   structure, not absence.
5. **Singular accent** — Exactly ONE element per image gets a filled,
   crayon-like block of color. Never two.
6. **Style character** — Raw, quick, conceptual. Marks look decided, not
   labored — as if drawn in under a minute by someone who knows the subject.

## Color system (strict roles)

| # | Color   | Hex       | Role            | Usage in illustration |
|---|---------|-----------|-----------------|------------------------|
| 1 | Indigo  | `#30197C` | Dominant (60%) — "Core" | All contour lines / drawn edges |
| 2 | Cyan    | `#41C5EE` | Secondary (30%) — "Action" | The single ground/environment brush stroke |
| 3 | Magenta | `#ff0082` | Accent (10%) — "Creativity/STEAM" | The one crayon-like fill per image |
| 4 | Amber   | `#ffd200` | Utility (1%) — "Critical alerts" | Never decorative; reserved for urgency |

Background: plain, textured off-white.

## Anatomy of every illustration (fixed sequence)

1. **Subject** — person/character/object as a single continuous Indigo line, no fill.
2. **Object/scenario** — one relevant object beside the subject, same contour treatment.
3. **Accent element** — one meaningful part (backpack, screen, lightbulb) filled
   with textured Magenta crayon-like color. The ONLY fill in the image.
4. **Environment** — one broad horizontal Cyan brush stroke beneath the subject,
   implying the entire location (floor, horizon, table). One stroke only.

## Prompt template

```
Minimalist line art doodle on a plain, textured off-white background.
[SUBJECT], drawn with a single continuous fluid Indigo (#30197C) line, [ACTION].

Beside [PRONOUN] is a [OBJECT/SCENARIO].

The composition uses the absolute minimum number of strokes — essential lines
only, leaving vast empty space. One element, [ACCENT ELEMENT], is filled with a
textured Magenta (#ff0082) crayon-like block of color.

A final, single, broad Cyan (#41C5EE) brush stroke defines the [GROUND TYPE]
beneath them, suggesting [LOCATION] with extreme economy.

Style is raw, quick, and conceptual; zero rendering, zero shading.
```

Variables:
- `[SUBJECT]` — e.g. a 9-year-old girl / a teacher / a small robot
- `[ACTION]` — e.g. sitting at a desk / jumping for joy / holding a tablet
- `[OBJECT/SCENARIO]` — e.g. a small tech gadget / a stack of books / a futuristic terminal
- `[ACCENT ELEMENT]` — e.g. the backpack / the gadget screen / a lightbulb
- `[GROUND TYPE]` — e.g. floor line / horizon / table surface
- `[LOCATION]` — e.g. a laboratory / home / outer space

## What breaks the system (never do)

- ❌ Multiple filled areas — the Magenta fill has power because it appears once
- ❌ Shading, hatching, gradients, or drop shadows
- ❌ More than one Cyan environment stroke
- ❌ Background detail — no patterns, textures, or secondary scenes
- ❌ Amber used decoratively — it signals critical importance only
- ❌ Overly precise/digital lines — marks must feel immediate and gestural
