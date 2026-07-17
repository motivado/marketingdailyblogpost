import os, sys, json, base64, urllib.request, urllib.error

API_KEY = os.environ["GEMINI_API_KEY"]
MODEL = "gemini-3-pro-image"

STYLE = """Minimalist single-continuous-line art doodle, hand-drawn, on a plain textured off-white paper background. Subject: {SUBJECT}.

CRITICAL STYLE: each character and object is drawn with a SINGLE continuous fluid line in deep indigo (#30197C) — one unbroken, confident, gestural stroke per figure, like a quick one-line contour sketch done without lifting the pen. Use the absolute minimum number of strokes to define each form, essential lines only. Leave vast empty white space around everything. Raw, quick, conceptual, loose and imperfect — like a designer doodle, NOT a polished vector illustration, NOT a cartoon with filled shapes.

Zero rendering: no shading, no hatching, no gradients, no fill on the figures — they are pure outline only.

ONE single accent: {ACCENT} is filled with a textured magenta (#ff0082) crayon-like block of color, rough and uneven like a wax crayon scribble. This is the only filled color area in the whole image.

A final single broad horizontal cyan (#41C5EE) brush stroke sits beneath the figures to suggest {GROUND}, painted with extreme economy in one gesture.

Flat, no perspective, no furniture, no background objects, no patterns. No text, no words, no letters, no numbers, no logos anywhere. 16:9 landscape, lots of negative space."""

JOBS = {
  "nb_nasa.png": dict(
    SUBJECT="a child crouching low to watch a small swarm of several tiny wheeled robots spreading out across the floor to explore together",
    ACCENT="one of the little swarm robots", GROUND="the floor of a classroom"),
  "nb_catapult.png": dict(
    SUBJECT="a parent and a child leaning in together, having just fired a small desktop catapult that flings a little ball arcing through the air",
    ACCENT="the small ball flying through the air", GROUND="a table surface"),
  "nb_water.png": dict(
    SUBJECT="two children building a simple DIY water dispenser from an upside-down plastic bottle, a drip of water falling into a cup below",
    ACCENT="the plastic water bottle", GROUND="a table surface"),
  "nb_conf.png": dict(
    SUBJECT="an educator standing and gesturing while presenting at an education conference, showing a small robot on a display stand to a couple of listeners",
    ACCENT="the small robot on the display stand", GROUND="the floor of a conference hall"),
}

def gen(prompt, out):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"
    payload = {"contents":[{"parts":[{"text":prompt}]}],
               "generationConfig":{"responseModalities":["IMAGE"],"imageConfig":{"aspectRatio":"16:9"}}}
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                headers={"Content-Type":"application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = json.load(resp)
    for cand in data.get("candidates", []):
        for part in cand.get("content", {}).get("parts", []):
            inline = part.get("inlineData") or part.get("inline_data")
            if inline and inline.get("data"):
                open(out,"wb").write(base64.b64decode(inline["data"])); return True
    return False

for out, v in JOBS.items():
    p = STYLE.format(**v)
    try:
        ok = gen(p, out)
        print(("SAVED " if ok else "NOIMG ") + out)
    except urllib.error.HTTPError as e:
        print("HTTP", e.code, out, e.read().decode()[:120])
