# Scheduled task prompt

This is the text that should live in the **account scheduler** (claude.ai →
Schedules → the TokyLabs daily blog task). It is deliberately tiny: the repo is
the single source of truth, so the routine can change without anyone editing the
schedule.

Claude cannot edit the account scheduler from inside a session — `CronList` only
ever sees session-local jobs. Updating the schedule is a manual step in the UI.

---

## Paste this as the scheduled prompt

```
Publish today's TokyLabs blog post.

Working directory: github.com/motivado/marketingdailyblogpost
Read TASK.md in that repo and follow it exactly — it is the single source
of truth for this routine. Do not rely on any steps quoted in this prompt;
TASK.md supersedes them.

Non-negotiables:
- One article per day, maximum.
- Never expose SELLDONE_TOKEN or GEMINI_API_KEY in output, commits, or logs.
- Commit and push to the repo — it is the only storage that survives the run.

Finish by summarising: title, Selldone article ID, source, cover image, and
anything that needs a human (expired feeds, exhausted idea lists, API errors).
```

---

## Why this shape

The previous scheduled prompt inlined the whole routine. It drifted out of sync
with `TASK.md` — on 2026-08-24 it was missing Step 5.5 entirely, so the run
published without a cover image and had no way to know it should have made one.

Keeping the schedule thin means:

* `TASK.md` is edited in one place, reviewed in git, and takes effect next run.
* Environment secrets stay in environment settings, never in prompt text.
* The scheduler holds only what a scheduler should: when to run and where to look.
