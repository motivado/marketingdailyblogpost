# TokyLabs Daily Blog — Task Instructions (v2)

> Drop-in replacement for the original daily prompt. Same content rules,
> corrected mechanics based on what actually works in the Claude Code cloud
> environment (verified 2026-07-13, article ID 738835 published successfully).

## WHO IS TOKYLABS

TokyLabs is a Bali-based edtech company that fights for the future of learning
by teaching the most useful skills to youngsters through fun robotics:

* **Tokymaker** — robotics kits for secondary school students
* **Tokymini** — screenless robotics kits for primary school students
* **Teacher training** — STEM robotics certification programs
* **After-school activities** — teachers who go to international schools to teach fun robotics
* Website: tokylabs.com

Tone: warm, inspiring, educator-friendly. Audience: parents, teachers, school administrators.

## CONFIGURATION

Set these as **environment secrets** in the Claude Code environment settings —
never paste the token into the prompt text, a file, or a log.

The scheduled prompt itself should stay thin and just point here — see
`SCHEDULED_PROMPT.md` for the exact text and why. Claude cannot edit the account
scheduler from a session; that is a manual step in the claude.ai UI.

```
SELLDONE_TOKEN=<secret — Bearer token, backoffice:shop:write scope>
GEMINI_API_KEY=<secret — used by scripts/gen_cover.py for cover images>
SELLDONE_SHOP_ID=2362
RSS_FEED_TOKYLABS=https://rss.app/feeds/<ID>.xml        # note /feeds/ + .xml — see RSS section
RSS_FEED_TOKYLABS_BALI=https://rss.app/feeds/<ID>.xml
LANGUAGE=English
```

## YOUR TASK

Run once per day and publish **one** blog article to the TokyLabs Selldone blog
(shop ID 2362) at https://tokylabs.com/blog.

### STEP 0 — CHECK WHAT WAS ALREADY PUBLISHED (dedup)

The cloud container is ephemeral: `~/Documents` does **not** persist between
runs, so a local log file cannot be the source of truth. Instead:

1. `GET https://api.selldone.com/shops/2362/blogs` (Bearer auth) — returns all
   existing articles with titles. **Never repeat one of these titles.**
2. Read `log/blog-log.txt` in this repo (committed after each run) for used
   ebook sections and Notion ideas.

### STEP 1 — READ NOTION FOR CONTENT IDEAS

Use the **Notion MCP connector** (no NOTION_TOKEN needed inside Claude Code).

⚠️ Known limitation: `notion-query-data-sources` / `notion-query-database-view`
require a Notion Business plan and will fail with a 400. **Use `notion-fetch`
on the pages and `notion-search` instead** — they work on the current plan.

Page: https://www.notion.so/tokylabs/GTE-Marketing-View-251f65d7fc2080288891c6212a8d11ec

* 📨 **Newsletter Ideas** (collection `261f65d7-fc20-8038-9b30-000b3cb15a1d`):
  entries where `Used?` = false. Fields: `Idea`, `Section` (Trivia, Cool Stuff,
  Philosophical Note, What's New?, Fam. Project).
* 📷 **Instagram Ideas** (collection `333f65d7-fc20-8056-83ba-000bc4b9f776`):
  entries where `Status` ≠ "Posted". Prioritize "Approved".

If **every** newsletter idea is marked Used (this was the case on 2026-07-13),
note it in the log and in your final summary so fresh ideas get added.

### STEP 2 — CHECK RSS FEEDS FOR NEW INSTAGRAM POSTS

Fetch both feeds. A post is "new" if published today or yesterday.

⚠️ The URLs must be the **saved-feed XML format**: `https://rss.app/feeds/<ID>.xml`.
The old `https://rss.app/feed/<ID>` links were unsaved previews and return
"Feed not saved" — feeds must be created while logged into the rss.app account.
If a feed returns HTML or an error instead of XML, log it and fall back to STEP 5.

New posts found → STEP 3. No new posts → STEP 5.

### STEP 3 — EXTRACT POST CONTENT

For the most recent new post: full caption, all images, carousel check.
Carousel rule: one article per image — same caption, each article focuses on
what its image shows. (Still max one article published per day; queue extras
as drafts in `drafts/` in this repo.)

### STEP 4 — WRITE ARTICLE(S) FROM INSTAGRAM

* **Title**: specific, compelling, tied to the image/caption. Not already on the blog (STEP 0).
* **Hook** (1 paragraph): bold statement, question, or surprising fact.
* **Body — Learning / Tips** (2–3 paragraphs): what skill the activity develops,
  why hands-on/robotics learning matters, practical tips for teachers or parents.
  Cross-reference unused Notion Newsletter Ideas; if one fits, weave it in and
  mark it `Used?` = true after publishing (via `notion-update-page`).
* **TokyLabs mention** (1 paragraph): warm, natural close. Vary the angle daily —
  Tokymaker, Tokymini, teacher training, or after-school programs.
* **Length**: 300–500 words. **Image**: the Instagram image from RSS; omit if
  unavailable — never fabricate.

### STEP 5 — PUBLISH FROM DRAFT QUEUE, OR WRITE FROM EBOOK + NOTION (no new Instagram post)

**First, check the draft queue.** `drafts/*.md` are ready-to-publish articles
with YAML front matter (`title`, `posted`, `body_format`, `origin_date`). If
any draft has `posted: false`, publish the one with the oldest `origin_date` —
a finished article beats generating a new one. The file body below the front
matter is the article content: if `body_format: html` publish as-is; if
`body_format: markdown` convert it to HTML first. After publishing, set
`posted: true`, add `posted_date`, `selldone_article_id`, and `slug` to its
front matter, and commit.

If every draft is already `posted: true`, write a new article instead:

The ebook is in this repo: **`content/tokylabs_ebook.md`** (markdown — use
this one; it's searchable and chapter-structured). The original PDFs are in
`ebook/` for reference.

Topic priority:
1. Approved Instagram Idea in Notion → use as topic angle, find matching ebook section
2. Unused Newsletter Idea in Notion → use as topic, find matching ebook section
3. Unused ebook section directly (check `log/blog-log.txt` for used sections)

Same structure as STEP 4: Hook → Learning/Tips → TokyLabs mention.

### STEP 5.5 — COVER IMAGE (for any article that has none)

⚠️ **Do this BEFORE Step 6, always.** Selldone has no update endpoint — see the
warning in Step 6 — so an image that is not in the create call can never be
added to that article afterwards. Generate the cover first, then publish once.

Articles from Instagram already have a photo (Step 4). For all others (draft
queue, Notion, ebook), generate a cover with **Gemini (Nano Banana)**:

```bash
python3 scripts/gen_cover.py "<slug>" "<ACTION>" "<KEY ELEMENT>"
```

It prints the path it wrote and the public raw.githubusercontent URL. Commit and
push the image **before** Step 6 so the URL resolves when the article goes live,
then pass that URL as `image` in the create call.

* Needs `GEMINI_API_KEY` as an environment secret (already set).
* Default model `gemini-3.1-flash-image` (Nano Banana 2); override with
  `GEMINI_IMAGE_MODEL`. `gemini-3-pro-image` follows instructions best,
  `gemini-3.1-flash-lite-image` is fastest.
* Set `BLOG_BRANCH` to the branch you are pushing to so the printed URL matches
  (defaults to `main`).
* The API returns JPEG, so the file is written as `.jpg` — use the exact
  filename the script prints, don't assume `.png`.
* `ai.google.dev` is blocked by the sandbox egress proxy, but the API host
  `generativelanguage.googleapis.com` is reachable. Don't try to read the docs.

Canva MCP was the previous method and is no longer used — it hit an account
quota limit on 2026-08-24 and blocked cover generation entirely.

**Cover image prompt template** — this is what `gen_cover.py` sends; it is
reproduced here so the wording stays reviewable. Keep the two in sync.

> Minimalist black line art doodle on a plain, textured off-white background.
> A main character, drawn with a single continuous fluid black line, is
> [ACTION related to the article topic]. The composition uses the absolute
> minimum number of strokes to define forms — essential lines only, leaving
> vast empty space. One key element ([KEY ELEMENT]) is filled with a textured
> magenta (#FF0082) crayon-like block of color. A final, single, broad magenta
> (#FF0082) brush stroke defines the environment beneath them, suggesting the
> location with extreme economy. Style is raw, quick, and conceptual; zero
> rendering, zero shading. No readable text or logos.

Brand color reference: `brand/colors.md`. The magenta `#FF0082` is TokyLabs'
Creativity/STEAM accent — use it consistently for the filled element and ground
stroke in every cover image. The model approximates the hex rather than matching
it exactly; the centring instruction at the end of the template matters, without
it the subject crowds one edge.

The repo is public, so the raw URL is visible to blog readers. Prefer the
default branch (`claude/trusting-cannon-fgGop`) once the image is merged there;
a working-branch URL resolves immediately but breaks if the branch is deleted.

**Never block publishing on images**: if generation fails, publish without an
image and note it in the log — but note the article then cannot be fixed later,
so retry generation once before giving up.

### STEP 6 — PUBLISH TO SELLDONE

**Verified working endpoint** (the old `POST /shops/2362/blogs` returns 404):

```
POST https://api.selldone.com/article/shop-blog/edit
Authorization: Bearer <SELLDONE_TOKEN>
Content-Type: application/json

{
  "shop_id": 2362,
  "parent_type": "shop-blog",
  "parent_id": 28661,
  "title": "[article title]",
  "body": "[article body in HTML]",
  "image": "[image URL if available]",
  "published": true
}
```

🚨 **This endpoint only ever CREATES. There is no update.** Passing an existing
`id` in the body is silently ignored and you get a second article with the same
title — this is where every duplicate pair on the blog came from (743279/743280,
744797/744798, 743879/745469, and one on 2026-08-24). Verified 2026-08-24: no
`/article/shop-blog/{id}/edit` or `/edit/{id}` route exists (both 404).

Consequences:
* **Publish exactly once per article, with `image` already filled in.** A cover
  cannot be attached after the fact — do Step 5.5 first.
* To fix a published article you must `DELETE https://api.selldone.com/article/shop-blog/{id}`
  (returns `{"success":true,"id":...}`) and create it again. Deleting frees the
  slug, so delete before recreating to keep the clean slug.
* Before doing that on anything not published in the current run, ask first.

Notes:
* `shop_id` is **required** in the body (its absence is the only validation error).
* `parent_id` is required but the server assigns a fresh shop-blog wrapper per
  article on create — any existing id (e.g. 28661) works as the placeholder.
* Success response: `{ "id": <article_id>, "article": { ..., "slug": ... } }`.
* Only `api.selldone.com` is reachable from the sandbox; `xapi.selldone.com`
  and `backoffice.selldone.com` are blocked by the network policy — don't try them.
* On error: save the draft to `drafts/YYYY-MM-DD.md` in this repo and log the failure.

### STEP 7 — LOG THE RESULT (in the repo, then push)

Append to `log/blog-log.txt` **in this repository**, then commit and push —
this is the only storage that survives between daily runs:

```
[DATE] Source: Instagram @tokylabs / single image
[DATE] Title: "..."  | Selldone article ID: ...
[DATE] Notion Newsletter Idea used: ... (or n/a)
[DATE] Ebook section used: ... (or n/a)
[DATE] Status: Published ✅ (or Failed ❌ + reason)
```

## RULES

* One article per day maximum.
* Instagram always takes priority over ebook/Notion.
* Notion ideas enrich articles — they don't replace Instagram content.
* Never repeat a title already on the blog (check via API, STEP 0) or an ebook
  section already in `log/blog-log.txt`.
* Never fabricate TokyLabs facts.
* Vary the closing paragraph daily.
* **Never log or expose the Selldone token** — not in output, commits, drafts, or logs.

## KNOWN OPEN ITEMS (need a human once)

1. ~~rss.app feeds~~ ✅ Fixed 2026-07-13: saved feeds at
   `https://rss.app/feeds/ZOW2f9aPjd0Eu1F1.xml` (@tokylabs) and
   `https://rss.app/feeds/dtcuQF1bcNy66AOd.xml` (@tokylabs.bali).
2. ~~Notion content~~ ✅ Fixed 2026-07-13: 8 fresh Newsletter Ideas added.
3. ~~Ebook~~ ✅ Fixed 2026-07-13: `content/tokylabs_ebook.md` (+ PDFs in `ebook/`).
4. **Secrets**: still pending — regenerate SELLDONE_TOKEN in Selldone (the old
   one appeared in plaintext prompts) and store it as an environment secret,
   never in the prompt text.
