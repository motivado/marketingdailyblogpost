# Gemini Cover Image Generation ("Nano Banana")

> **What this is**: the system used to generate blog cover images for the
> TokyLabs daily blog post routine. Replaces the previous Canva MCP step
> (dropped 2026-08-24 after hitting an account quota limit).

---

## Quick-reference

| Item | Value |
|------|-------|
| Script | `scripts/gen_cover.py` |
| API endpoint | `https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent` |
| Default model | `gemini-3.1-flash-image` (Nano Banana 2) |
| Credential env var | `GEMINI_API_KEY` |
| Output location | `images/covers/<slug>.<ext>` |
| Output format | JPEG (the API decides — script detects MIME type automatically) |

---

## Credentials

### `GEMINI_API_KEY`

- **What it is**: a Google AI Studio API key with access to Gemini image
  generation models.
- **Where to get it**: [Google AI Studio](https://aistudio.google.com) →
  *Get API key*. The key starts with `AIza…`.
- **How it is stored**: as a **Claude Code environment secret** — set it in
  the project's environment settings in claude.ai, never paste it into
  a file, commit, log, or chat message.
- **Scope needed**: the key only needs Generative Language API access. No
  OAuth, no service account — a plain API key is sufficient.
- **Sandbox note**: `ai.google.dev` (the docs site) is blocked by the
  Claude Code cloud egress proxy. The API host
  `generativelanguage.googleapis.com` is reachable. Don't try to fetch
  docs at runtime.

### Optional: `GEMINI_IMAGE_MODEL`

Override the model by setting this env var. Leave unset to use the default.

| Value | Nickname | Trade-off |
|-------|----------|-----------|
| `gemini-3.1-flash-image` | Nano Banana 2 | **Default** — good quality/latency balance |
| `gemini-3-pro-image` | Nano Banana Pro | Best prompt-following; slower |
| `gemini-3.1-flash-lite-image` | Nano Banana Lite | Fastest / cheapest |
| `gemini-2.5-flash-image` | Nano Banana 1 | Original; use only if newer models unavailable |

### Optional: `BLOG_BRANCH`

The script constructs the public `raw.githubusercontent.com` URL using the
current git branch. Set `BLOG_BRANCH` only if you are pushing the image to a
different branch than the one `git rev-parse HEAD` reports.

---

## How to generate a cover image

```bash
python3 scripts/gen_cover.py "<slug>" "<ACTION>" "<KEY ELEMENT>"
```

| Argument | What it means |
|----------|---------------|
| `<slug>` | The article's URL slug, e.g. `why-joy-is-the-secret-ingredient` |
| `<ACTION>` | A vivid present-participle phrase describing what the main character is doing, e.g. `"leaping with arms outstretched beside a small robot"` |
| `<KEY ELEMENT>` | The single object that gets the magenta fill, e.g. `"the small robot"` |

**Example**:
```bash
python3 scripts/gen_cover.py \
  "your-school-says-it-teaches-robotics-3-questions" \
  "looking through a large magnifying glass at a tiny robot on a desk with a curious expression" \
  "the magnifying glass"
```

The script prints the file path it wrote and the public URL to use:

```
model: gemini-3.1-flash-image
slug:  your-school-says-it-teaches-robotics-3-questions

wrote /…/images/covers/your-school-says-it-teaches-robotics-3-questions.jpg  (631,979 bytes, image/jpeg)

Commit and push to 'claude/clever-keller-eptli4' BEFORE publishing, then use:
https://raw.githubusercontent.com/motivado/marketingdailyblogpost/claude/clever-keller-eptli4/images/covers/your-school-says-it-teaches-robotics-3-questions.jpg
```

---

## Critical ordering rule

> **Always generate and push the cover image BEFORE calling the Selldone
> publish endpoint.**

Selldone's `/article/shop-blog/edit` endpoint creates-only — there is no
update. An `image` field omitted from the create call can never be added to
that article afterwards. The raw.githubusercontent URL 404s until the commit
is pushed, so the sequence must be:

1. Run `scripts/gen_cover.py` → image written to `images/covers/`
2. `git add images/covers/<slug>.jpg && git commit && git push`
3. Call the Selldone API with the `image` URL in the body

---

## Brand prompt template

The script sends this prompt verbatim (see `PROMPT_TEMPLATE` in the script):

```
Minimalist Indigo #30197C line art doodle on a plain, textured off-white
background. A main character, drawn with a single continuous fluid Indigo
#30197C line, is {action}. The composition uses the absolute minimum number
of strokes to define forms — essential lines only, leaving vast empty space.
One key element ({key_element}) is filled with a textured magenta (#FF0082)
crayon-like block of color. A final, single, broad cyan (#41C5EE) brush
stroke defines the environment beneath them, suggesting the location with
extreme economy. Style is raw, quick, and conceptual; zero rendering, zero
shading. No readable text or logos. Centre the subject in the frame with
balanced margins on both sides.
```

### Brand color roles (from `brand/colors.md`)

| Color | Hex | Role in cover |
|-------|-----|---------------|
| Indigo | `#30197C` | Line art / all doodle strokes (dominant) |
| Cyan | `#41C5EE` | Single ground brush stroke beneath the character |
| Magenta | `#FF0082` | Crayon fill on the one KEY ELEMENT (accent) |

All three colors must appear in every cover. The model approximates each hex;
the centring instruction at the end of the prompt is important — without it
the subject crowds one edge.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `GEMINI_API_KEY is not set` | Env var missing | Set it as a Claude Code environment secret |
| `HTTP 400: …` | Bad request body | Check that `action` and `key_element` are non-empty strings |
| `HTTP 403: …` | Key invalid or API not enabled | Regenerate key in Google AI Studio; enable Generative Language API |
| `HTTP 429: …` | Rate limit | Script retries automatically (3 attempts, exponential backoff) |
| `ai.google.dev` unreachable | Proxy blocks docs host | Expected — use the API host `generativelanguage.googleapis.com` directly |
| URL 404 after publishing | Image not pushed before publish | Delete the Selldone article, push the image commit, recreate the article |
| Cover not visible on article | `image` field missing from create call | Cannot be fixed without deleting and recreating the article |

---

## Where covers are stored

```
images/covers/<slug>.jpg   ← committed to this repo, publicly readable via
                              raw.githubusercontent.com on any pushed branch
```

The repo is public, so the raw URL is visible to blog readers. Images on the
default branch (`claude/trusting-cannon-fgGop`) persist even after working
branches are deleted. Working-branch URLs resolve immediately and are safe to
use in the same run, but break if that branch is later removed.

---

## How this fits in the daily blog routine

See `TASK.md` Step 5.5 for the authoritative description. This document is
the engineering companion: credentials, API mechanics, and the script
internals. `TASK.md` is the single source of truth for the overall process.
