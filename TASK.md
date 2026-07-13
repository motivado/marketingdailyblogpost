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

```
SELLDONE_TOKEN=<secret — Bearer token, backoffice:shop:write scope>
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

### STEP 5 — WRITE ARTICLE FROM EBOOK + NOTION (no new Instagram post)

⚠️ The ebook must live at `ebook/tokylabs-ebook.pdf` **in this repo** — the old
config pointed at a macOS path (`/Users/eduardo/...`) which does not exist in
the cloud container. Until the PDF is committed, skip the ebook and use Notion
ideas or the pre-written articles in `daily_blog.py`.

Topic priority:
1. Approved Instagram Idea in Notion → use as topic angle, find matching ebook section
2. Unused Newsletter Idea in Notion → use as topic, find matching ebook section
3. Unused ebook section directly (check `log/blog-log.txt` for used sections)

Same structure as STEP 4: Hook → Learning/Tips → TokyLabs mention.

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

1. **rss.app**: log in and recreate both Instagram feeds so they're saved to the
   account; put the `https://rss.app/feeds/<ID>.xml` URLs into the environment config.
2. **Notion content**: all Newsletter Ideas are marked Used — add fresh ideas.
3. **Ebook**: commit the PDF to `ebook/tokylabs-ebook.pdf` in this repo.
4. **Secrets**: move SELLDONE_TOKEN out of the prompt text and into the
   environment's secret variables.
