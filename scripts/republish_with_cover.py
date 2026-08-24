#!/usr/bin/env python3
"""Attach a cover image to an already-published Selldone article.

Selldone's /article/shop-blog/edit endpoint has no update mode — passing an
existing id is ignored and you get a duplicate (see TASK.md Step 6). The only
way to change a published article is to delete it and create it again, which
also frees its slug so the replacement keeps the same URL.

That makes this destructive and unavoidably so. It refuses to run on anything
whose exact body is not recoverable from drafts/, and it prints a plan and
requires --commit before touching the live blog.

Usage:
    python3 scripts/republish_with_cover.py            # dry run, prints plan
    python3 scripts/republish_with_cover.py --commit   # actually republish

Requires SELLDONE_TOKEN. Cover images must already be pushed and resolving at
IMAGE_BASE, or the articles go live with broken images.
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

SHOP_ID = 2362
API = "https://api.selldone.com"
BRANCH = os.environ.get("BLOG_BRANCH", "claude/trusting-cannon-fgGop")
IMAGE_BASE = (
    "https://raw.githubusercontent.com/motivado/marketingdailyblogpost"
    f"/{BRANCH}/images/covers"
)

# article id -> (draft filename, cover basename)
# Duplicate pairs intentionally share a cover; each live article is preserved.
PLAN = [
    (745683, "kids-hackathons.md", "kids-hackathons.jpg"),
    (745469, "upcycling-stem.md", "upcycling-stem.jpg"),
    (744993, "robot-builds-brain.md", "robot-builds-brain.jpg"),
    (744798, "robotics-teacher-demand.md", "robotics-teacher-demand.jpg"),
    (744797, "robotics-teacher-demand.md", "robotics-teacher-demand.jpg"),
    (744544, "effort-ai-age.md", "effort-ai-age.jpg"),
    (743879, "upcycling-stem.md", "upcycling-stem.jpg"),
    (743718, "microrobots.md", "microrobots.jpg"),
]

# 744103 "Why the Flipped Classroom Is the Future of Robotics Education" is
# deliberately absent: it was written straight from the ebook and never saved
# as a draft, so its body exists only inside Selldone and cannot be recreated.
# Deleting it would destroy it. Leave it alone.

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_draft(name):
    """Return (title, body_html) from a draft, or raise if unusable."""
    path = os.path.join(REPO, "drafts", name)
    text = open(path, encoding="utf-8").read()
    if not text.startswith("---"):
        raise SystemExit(f"{name}: no front matter")
    _, fm, body = text.split("---", 2)

    title = re.search(r"^title:\s*(.+)$", fm, re.M).group(1).strip()
    # Unwrap the YAML quoting style used across these drafts.
    if title[:1] == title[-1:] and title[:1] in "'\"":
        quote, title = title[0], title[1:-1]
        title = title.replace(quote * 2, quote)

    fmt = re.search(r"^body_format:\s*(\w+)", fm, re.M)
    if not fmt or fmt.group(1) != "html":
        raise SystemExit(f"{name}: body_format is not html — convert first")

    # Drop the trailing provenance block; it is notes, not article text.
    body = re.split(r"\n---\s*\n\*\*Source:", body)[0].strip()
    if len(body) < 500:
        raise SystemExit(f"{name}: body suspiciously short ({len(body)})")
    return title, body


def call(method, path, payload=None, token=None, retries=4):
    url = f"{API}{path}"
    data = json.dumps(payload).encode() if payload is not None else None
    headers = {"Authorization": f"Bearer {token}"}
    if data:
        headers["Content-Type"] = "application/json"
    last = None
    for attempt in range(retries):
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}: {e.read().decode()[:300]}"
            if e.code < 500:
                raise SystemExit(f"{method} {path} — {last}")
        except Exception as e:
            last = str(e)
        if attempt < retries - 1:
            time.sleep(2 ** (attempt + 1))
    raise SystemExit(f"{method} {path} failed after {retries} tries — {last}")


def check_image(url):
    try:
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=45) as r:
            return r.status == 200
    except Exception:
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", action="store_true", help="actually republish")
    args = ap.parse_args()

    token = os.environ.get("SELLDONE_TOKEN")
    if not token:
        raise SystemExit("SELLDONE_TOKEN is not set.")

    print(f"branch: {BRANCH}\n")

    # Resolve everything up front — a failure here must not leave the blog
    # with some articles deleted and others not.
    jobs = []
    for aid, draft, cover in PLAN:
        title, body = load_draft(draft)
        url = f"{IMAGE_BASE}/{cover}"
        jobs.append((aid, title, body, url))
        print(f"  [{aid}] {len(body):5}B  {cover:32} {title[:44]}")

    print("\nverifying cover URLs resolve...")
    missing = {u for _, _, _, u in jobs if not check_image(u)}
    if missing:
        print("\nThese covers do not resolve — push them to "
              f"{BRANCH} first, or the articles go live broken:")
        for u in sorted(missing):
            print(f"  404  {u}")
        raise SystemExit(1)
    print("  all resolve ✓")

    if not args.commit:
        print(f"\nDry run. {len(jobs)} articles would be deleted and recreated.")
        print("Re-run with --commit to apply.")
        return

    print()
    for aid, title, body, url in jobs:
        d = call("DELETE", f"/article/shop-blog/{aid}", token=token)
        if not d.get("success"):
            raise SystemExit(f"delete {aid} failed: {d}")

        r = call("POST", "/article/shop-blog/edit", {
            "shop_id": SHOP_ID,
            "parent_type": "shop-blog",
            "parent_id": 28661,
            "title": title,
            "body": body,
            "image": url,
            "published": True,
        }, token=token)
        if r.get("error"):
            # The body is safe in drafts/ — recreate by hand from the plan.
            raise SystemExit(
                f"CREATE FAILED after deleting {aid}: {r.get('error_msg')}\n"
                f"Article {aid} is deleted. Recreate it from its draft."
            )
        art = r["article"]
        print(f"  {aid} -> {r['id']}  slug={art['slug']}")

    print("\nDone.")


if __name__ == "__main__":
    main()
