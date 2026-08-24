#!/usr/bin/env python3
"""Generate a blog cover image with Gemini (Nano Banana).

Replaces the Canva MCP step in the daily blog routine — same brand style,
no quota ceiling, no signed-URL download race.

Usage:
    python3 scripts/gen_cover.py <slug> "<ACTION>" "<KEY ELEMENT>"

Example:
    python3 scripts/gen_cover.py why-joy-is-the-secret \
        "leaping with arms outstretched in joyful delight beside a small robot" \
        "the small robot"

Writes images/covers/<slug>.png and prints the raw.githubusercontent URL.

Requires GEMINI_API_KEY in the environment (set as a Claude Code env secret).
"""

import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request

# Nano Banana 2 — good quality/latency balance. Alternatives:
#   gemini-3-pro-image          (Nano Banana Pro — best instruction following)
#   gemini-3.1-flash-lite-image (fastest/cheapest)
#   gemini-2.5-flash-image      (original Nano Banana)
MODEL = os.environ.get("GEMINI_IMAGE_MODEL", "gemini-3.1-flash-image")
API = "https://generativelanguage.googleapis.com/v1beta/models/{}:generateContent"

REPO_RAW = (
    "https://raw.githubusercontent.com/motivado/marketingdailyblogpost"
    "/{branch}/images/covers/{name}"
)

# The API picks the encoding itself, so name the file after what it actually
# returned rather than assuming PNG.
EXT = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp"}

# Verbatim brand template from TASK.md STEP 5.5. Keep in sync with that file.
PROMPT_TEMPLATE = (
    "Minimalist Indigo #30197C line art doodle on a plain, textured off-white "
    "background. A main character, drawn with a single continuous fluid Indigo "
    "#30197C line, is {action}. The composition uses the absolute minimum "
    "number of strokes to define forms — essential lines only, leaving vast "
    "empty space. One key element ({key_element}) is filled with a textured "
    "magenta (#FF0082) crayon-like block of color. A final, single, broad cyan "
    "(#41C5EE) brush stroke defines the environment beneath them, suggesting "
    "the location with extreme economy. Style is raw, quick, and conceptual; "
    "zero rendering, zero shading. No readable text or logos. Centre the "
    "subject in the frame with balanced margins on both sides."
)


def generate(prompt, api_key, retries=3):
    """POST to Gemini and return (image_bytes, mime_type)."""
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseModalities": ["IMAGE"],
            "imageConfig": {"aspectRatio": "16:9"},
        },
    }).encode()

    url = f"{API.format(MODEL)}?key={api_key}"
    last = None
    for attempt in range(retries):
        req = urllib.request.Request(
            url, data=body, headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                data = json.load(r)
            break
        except urllib.error.HTTPError as e:
            detail = e.read().decode()[:400]
            last = f"HTTP {e.code}: {detail}"
            # 4xx other than 429 won't fix themselves — fail fast.
            if e.code != 429 and e.code < 500:
                raise SystemExit(f"Gemini rejected the request — {last}")
        except Exception as e:  # network blip
            last = str(e)
        if attempt < retries - 1:
            time.sleep(2 ** (attempt + 1))
    else:
        raise SystemExit(f"Gemini unreachable after {retries} tries — {last}")

    for part in data["candidates"][0]["content"]["parts"]:
        inline = part.get("inlineData") or part.get("inline_data")
        if inline:
            return base64.b64decode(inline["data"]), inline.get("mimeType", "image/png")

    raise SystemExit(f"No image in response: {json.dumps(data)[:600]}")


def main():
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    slug, action, key_element = sys.argv[1:4]

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise SystemExit("GEMINI_API_KEY is not set in the environment.")

    prompt = PROMPT_TEMPLATE.format(action=action, key_element=key_element)
    print(f"model: {MODEL}\nslug:  {slug}\n")

    image, mime = generate(prompt, api_key)

    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_dir = os.path.join(repo, "images", "covers")
    os.makedirs(out_dir, exist_ok=True)
    name = slug + EXT.get(mime, ".png")
    out = os.path.join(out_dir, name)
    with open(out, "wb") as f:
        f.write(image)

    branch = os.environ.get("BLOG_BRANCH", "main")
    print(f"wrote {out}  ({len(image):,} bytes, {mime})")
    print(REPO_RAW.format(branch=branch, name=name))


if __name__ == "__main__":
    main()
