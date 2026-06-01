#!/usr/bin/env python3
"""
TokyLabs Daily Blog Publisher
Runs once per day: reads Notion ideas, checks Instagram RSS, writes and publishes
a blog article to the TokyLabs Selldone shop.
"""

import os
import json
import datetime
import pathlib
import textwrap
import feedparser
import requests
from notion_client import Client as NotionClient

# ── Config ────────────────────────────────────────────────────────────────────
SELLDONE_TOKEN = os.environ["SELLDONE_TOKEN"]
SELLDONE_SHOP_ID = os.environ.get("SELLDONE_SHOP_ID", "2362")
RSS_TOKYLABS = os.environ["RSS_FEED_TOKYLABS"]
RSS_TOKYLABS_BALI = os.environ["RSS_FEED_TOKYLABS_BALI"]
NOTION_TOKEN = os.environ["NOTION_TOKEN"]
LANGUAGE = os.environ.get("LANGUAGE", "English")

NEWSLETTER_DB = "261f65d7-fc20-8038-9b30-000b3cb15a1d"
INSTAGRAM_DB = "333f65d7-fc20-8056-83ba-000bc4b9f776"

LOG_FILE = pathlib.Path.home() / "Documents" / "tokylabs-blog-log.txt"
DRAFTS_DIR = pathlib.Path.home() / "Documents" / "tokylabs-drafts"
DRAFTS_DIR.mkdir(parents=True, exist_ok=True)

SELLDONE_API = f"https://api.selldone.com/shops/{SELLDONE_SHOP_ID}/blogs"


# ── Helpers ───────────────────────────────────────────────────────────────────
def today_str() -> str:
    return datetime.date.today().isoformat()


def log(message: str) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a") as f:
        f.write(f"[{today_str()}] {message}\n")
    print(f"[LOG] {message}")


def save_draft(title: str, body_html: str) -> pathlib.Path:
    path = DRAFTS_DIR / f"{today_str()}.md"
    path.write_text(f"# {title}\n\n{body_html}\n")
    return path


# ── Step 1: Notion — Newsletter Ideas (unused) ────────────────────────────────
def fetch_unused_newsletter_ideas(notion: NotionClient) -> list[dict]:
    response = notion.databases.query(
        database_id=NEWSLETTER_DB,
        filter={"property": "Used?", "checkbox": {"equals": False}},
    )
    ideas = []
    for page in response.get("results", []):
        props = page["properties"]
        ideas.append({
            "id": page["id"],
            "idea": props["Idea"]["title"][0]["plain_text"] if props["Idea"]["title"] else "",
            "section": props["Section"]["select"]["name"] if props["Section"].get("select") else "No Category yet",
        })
    return ideas


# ── Step 1: Notion — Instagram Ideas (not Posted) ────────────────────────────
def fetch_pending_instagram_ideas(notion: NotionClient) -> list[dict]:
    response = notion.databases.query(
        database_id=INSTAGRAM_DB,
        filter={"property": "Status", "status": {"does_not_equal": "Posted"}},
    )
    ideas = []
    for page in response.get("results", []):
        props = page["properties"]
        ideas.append({
            "id": page["id"],
            "name": props["Name"]["title"][0]["plain_text"] if props["Name"]["title"] else "",
            "status": props["Status"]["status"]["name"] if props["Status"].get("status") else "",
        })
    return sorted(ideas, key=lambda x: (x["status"] != "Approved", x["name"]))


# ── Step 2: RSS feed check ────────────────────────────────────────────────────
def fetch_new_posts(rss_url: str) -> list[dict]:
    """Return posts published today or yesterday.

    rss.app feeds require direct outbound access; they block cloud/proxy IPs.
    If the feed is unreachable the caller catches the exception and falls back.
    """
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    feed = feedparser.parse(rss_url, request_headers={"User-Agent": "TokyLabsBlogBot/1.0"})
    if feed.get("bozo") and not feed.entries:
        raise ConnectionError(f"RSS feed returned no entries (bozo={feed.bozo_exception})")
    new = []
    for entry in feed.entries:
        if not hasattr(entry, "published_parsed") or entry.published_parsed is None:
            continue
        pub = datetime.date(*entry.published_parsed[:3])
        if pub >= yesterday:
            images = []
            if hasattr(entry, "media_content"):
                images = [m["url"] for m in entry.media_content if "url" in m]
            elif hasattr(entry, "enclosures"):
                images = [e["href"] for e in entry.enclosures if "image" in e.get("type", "")]
            new.append({
                "title": entry.get("title", ""),
                "caption": entry.get("summary", ""),
                "images": images,
                "link": entry.get("link", ""),
                "published": pub.isoformat(),
            })
    return new


# ── Step 4: Write article from Instagram post ─────────────────────────────────
def write_article_from_instagram(
    post: dict,
    image_url: str | None,
    newsletter_idea: dict | None,
) -> tuple[str, str]:
    """Return (title, body_html)."""
    caption = post["caption"]
    notion_snippet = ""
    if newsletter_idea:
        notion_snippet = (
            f"<p><em>Fun fact: {newsletter_idea['idea']}</em></p>\n"
        )

    title = f"Hands-On Learning in Action: {post['title'][:60]}" if post["title"] else "Hands-On Robotics at TokyLabs"
    img_tag = f'<img src="{image_url}" alt="TokyLabs students" style="max-width:100%;">\n' if image_url else ""

    body = textwrap.dedent(f"""
        {img_tag}
        <p>{caption[:500]}</p>

        <h2>Why This Matters for Young Learners</h2>
        <p>Hands-on projects like this are where real learning happens. When children build, test, and improve something with their own hands, they develop problem-solving instincts, persistence, and creative confidence that no worksheet can replicate.</p>
        {notion_snippet}
        <h2>Bringing It Into the Classroom or Home</h2>
        <p>Teachers and parents don't need a high-tech lab to create these moments. Open-ended challenges — even simple ones with cardboard, wheels, or basic electronics — put children in the driver's seat of their own learning. The goal is not a perfect result; it's the thinking along the way.</p>

        <h2>TokyLabs After-School Activities</h2>
        <p>TokyLabs brings exactly this energy into international schools across Bali. Our team of trained educators leads after-school robotics sessions where students work with Tokymaker kits to design, build, and program real devices. Every session is a new challenge, and every challenge builds the skills children will rely on for life.</p>
    """).strip()

    return title, body


# ── Step 5: Write article from Notion idea ───────────────────────────────────
def write_article_from_notion(idea: dict) -> tuple[str, str]:
    """Return (title, body_html) for a newsletter idea or Instagram idea topic."""
    topic = idea["idea"] if "idea" in idea else idea["name"]
    section = idea.get("section", "")

    if "critical thinking" in topic.lower() or "think" in topic.lower():
        title = "Why Critical Thinking Is the Most Important Skill You Can Give Your Child in the Age of AI"
        body = textwrap.dedent("""
            <p>Your child is growing up in a world where artificial intelligence can answer almost any question in seconds. But here is what AI still cannot do: <em>think for your child</em>. The real advantage in tomorrow&rsquo;s world is not having the right answers &mdash; it&rsquo;s knowing how to ask the right questions, evaluate information, and make thoughtful decisions. Critical thinking is not a bonus skill anymore. It is the foundation.</p>

            <h2>What Critical Thinking Really Means for Kids</h2>
            <p>Critical thinking is the ability to analyze a situation, weigh evidence, and reach a reasoned conclusion &mdash; rather than simply accepting the first answer that appears. For children, this looks like questioning why something works the way it does, testing ideas, making mistakes, and trying again. It is less about raw intelligence and more about <em>how</em> a child approaches a problem.</p>
            <p>Research consistently shows that children who develop critical thinking skills early become more confident decision-makers, stronger communicators, and more adaptable learners. The good news? These skills are not taught through lectures. They are built through <em>doing</em>.</p>

            <h2>How Hands-On Learning Builds Young Thinkers</h2>
            <p>When a child builds a robot &mdash; even a simple screenless one &mdash; they are not following a script. They set a goal, design a solution, test it, observe what goes wrong, and iterate. This process, repeated across dozens of small projects, is how critical thinking becomes a habit rather than a lesson.</p>
            <p>The same principle drives real-world robotics challenges. NASA&rsquo;s Swarmathon challenged students to design algorithms for swarms of small robots solving coordination problems &mdash; the same search patterns used in space exploration. What made it powerful was not the technology itself, but the act of grappling with an open-ended problem and discovering a solution through persistence and creative reasoning. We can offer children that same experience at the right scale, from a very young age.</p>
            <p>For teachers and parents, the key is to resist giving the answer. When a child&rsquo;s robot does not behave as expected, that moment of confusion is the learning. Ask questions instead: <em>What do you think went wrong? What could we try differently?</em> The struggle is the point.</p>

            <h2>Practical Ways to Nurture a Critical Thinker at Home or in Class</h2>
            <ul>
            <li><strong>Introduce &ldquo;why&rdquo; conversations</strong> regularly &mdash; why does something work, what would happen if one thing changed?</li>
            <li><strong>Encourage low-stakes experimentation</strong>: building, cooking, gardening, or simple craft projects where children make decisions and observe outcomes.</li>
            <li><strong>Celebrate the curiosity to try again</strong> rather than the success itself &mdash; resilience and reflection are the real wins.</li>
            </ul>

            <h2>How TokyLabs Puts This Into Practice</h2>
            <p>At TokyLabs, building thinkers is at the heart of everything we do. Our Tokymini kits &mdash; screenless robotics designed for primary school children &mdash; remove the distraction of screens and focus entirely on physical interaction, cause-and-effect reasoning, and independent problem-solving. There are no step-by-step instructions to follow. Children explore, experiment, and figure things out with the support of trained mentors who know that the best answer is the one a child discovers on their own. Because a child who learns to think for themselves today becomes the confident, creative adult the world needs tomorrow.</p>
        """).strip()
    elif "swarm" in topic.lower() or "nasa" in topic.lower():
        title = "What NASA's Robot Swarms Can Teach Us About Educating Kids"
        body = textwrap.dedent("""
            <p>What if the best way to prepare children for the future was to let them solve real problems &mdash; the same kind engineers at NASA grapple with? It sounds ambitious, but the principle is simpler than you think.</p>

            <h2>The NASA Swarmathon: Real Students, Real Problems</h2>
            <p>NASA&rsquo;s Swarmathon is a competition where students design algorithms for swarms of small robots called Swarmies. These robots must coordinate to search an area efficiently &mdash; the same challenge faced by robots exploring distant planets. Students learn robotics, programming, and teamwork while solving a genuine, open-ended problem with no single correct answer.</p>
            <p>The results? Students who participate don&rsquo;t just learn code. They learn how to think like engineers: break a complex problem into parts, test hypotheses, collaborate under pressure, and adapt when things don&rsquo;t go as planned.</p>

            <h2>Bringing the Swarmathon Mindset to Any Classroom</h2>
            <p>You don&rsquo;t need a NASA budget to create this kind of learning. The key ingredients are: an open-ended challenge, the freedom to fail and iterate, and a teacher who asks questions rather than giving answers. A classroom robotics kit can replicate the same cognitive journey &mdash; setting goals, building a solution, watching it fail, and improving it.</p>
            <p>For teachers, this means resisting the urge to demonstrate the &ldquo;right&rdquo; way first. Give students the problem and the tools, then step back. The productive struggle is where the real learning happens.</p>

            <h2>TokyLabs Teacher Training</h2>
            <p>At TokyLabs, we believe every teacher can create this kind of environment &mdash; and we help them get there. Our STEM robotics certification programs give educators the confidence, tools, and techniques to facilitate open-ended challenges using Tokymaker in their own classrooms. Because when teachers shift from instructing to mentoring, the whole classroom transforms.</p>
        """).strip()
    else:
        title = f"The Power of {topic}: Why It Matters for Young Learners"
        body = textwrap.dedent(f"""
            <p>In a rapidly changing world, the skills that matter most are not the ones that can be Googled. They are the ones children build through experience, experimentation, and guided exploration. {topic} is one of those skills &mdash; and it starts earlier than most people think.</p>

            <h2>Why {topic} Matters</h2>
            <p>When children engage with challenges that have no single right answer, they build resilience, creativity, and the confidence to try again after a setback. These are the traits that define lifelong learners &mdash; and they are best developed through hands-on, open-ended experiences rather than passive instruction.</p>

            <h2>What Parents and Teachers Can Do</h2>
            <p>Start small. Introduce projects at home or in the classroom that give children ownership over the process. Let them make mistakes. Ask questions instead of providing answers. Celebrate effort and curiosity over correct outcomes. These small shifts in approach create big changes in how children engage with learning.</p>

            <h2>TokyLabs: Learning by Building</h2>
            <p>This philosophy is woven into everything TokyLabs creates. Whether through Tokymaker robotics kits for secondary students, Tokymini screenless kits for younger children, or after-school programs at international schools in Bali, TokyLabs puts children in charge of their own learning &mdash; guided by educators who know that the best lessons are the ones students discover themselves.</p>
        """).strip()

    return title, body


# ── Step 6: Publish to Selldone ───────────────────────────────────────────────
def publish_to_selldone(title: str, body_html: str, image_url: str | None = None) -> dict:
    payload: dict = {"title": title, "body": body_html, "published": True}
    if image_url:
        payload["image"] = image_url

    resp = requests.post(
        SELLDONE_API,
        headers={
            "Authorization": f"Bearer {SELLDONE_TOKEN}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=30,
    )
    if resp.status_code == 403:
        raise PermissionError(
            "Selldone API returned 403. Check that SELLDONE_TOKEN is valid and the "
            "network allows outbound HTTPS to api.selldone.com."
        )
    resp.raise_for_status()
    return resp.json()


# ── Step 7: Mark Notion idea as used ─────────────────────────────────────────
def mark_notion_idea_used(notion: NotionClient, page_id: str) -> None:
    notion.pages.update(page_id=page_id, properties={"Used?": {"checkbox": True}})


# ── Main workflow ─────────────────────────────────────────────────────────────
def main() -> None:
    notion = NotionClient(auth=NOTION_TOKEN)

    # Step 1: Read Notion
    newsletter_ideas = fetch_unused_newsletter_ideas(notion)
    instagram_ideas = fetch_pending_instagram_ideas(notion)
    approved_ig = [i for i in instagram_ideas if i["status"] == "Approved"]

    print(f"Newsletter ideas (unused): {len(newsletter_ideas)}")
    print(f"Instagram ideas (not posted): {len(instagram_ideas)}  |  Approved: {len(approved_ig)}")

    # Step 2: Check RSS feeds
    new_posts: list[dict] = []
    for rss_url in [RSS_TOKYLABS, RSS_TOKYLABS_BALI]:
        try:
            new_posts.extend(fetch_new_posts(rss_url))
        except Exception as exc:
            log(f"RSS fetch failed for {rss_url}: {exc}")

    title: str
    body_html: str
    image_url: str | None = None
    source_label: str
    notion_idea_used: dict | None = None

    if new_posts:
        # Step 3 & 4: Use most recent Instagram post
        post = new_posts[0]
        image_url = post["images"][0] if post["images"] else None

        # Cross-reference: find a matching unused newsletter idea
        for idea in newsletter_ideas:
            if any(kw in post["caption"].lower() for kw in idea["idea"].lower().split()[:3]):
                notion_idea_used = idea
                break
        if notion_idea_used is None and newsletter_ideas:
            notion_idea_used = newsletter_ideas[0]

        title, body_html = write_article_from_instagram(post, image_url, notion_idea_used)
        account = "@tokylabs.bali" if post in new_posts[len(new_posts)//2:] else "@tokylabs"
        source_label = f"Instagram {account} / {'carousel' if len(post['images']) > 1 else 'single image'}"
    else:
        # Step 5: Fallback — Notion ideas
        log("No new Instagram posts found. Using Notion idea fallback.")

        if approved_ig:
            topic_idea = {"idea": approved_ig[0]["name"], "section": "Instagram Idea"}
            source_label = f"Notion Instagram Idea (Approved): {approved_ig[0]['name']}"
        elif newsletter_ideas:
            # Prefer non-empty / rich ideas
            swarmathon = next((i for i in newsletter_ideas if "swarm" in i["idea"].lower() or "nasa" in i["idea"].lower()), None)
            topic_idea = swarmathon or newsletter_ideas[0]
            notion_idea_used = topic_idea
            source_label = f"Notion Newsletter Idea ({topic_idea['section']})"
        else:
            log("No unused Notion ideas available. Skipping today.")
            return

        title, body_html = write_article_from_notion(topic_idea)

    # Step 6: Publish
    try:
        result = publish_to_selldone(title, body_html, image_url)
        status = "Published"
        log(f"Source: {source_label}")
        log(f"Title: \"{title}\"")
        if notion_idea_used:
            log(f"Notion Newsletter Idea used: \"{notion_idea_used.get('section', '')} - {notion_idea_used.get('idea', '')}\"")
        log("Ebook section used: n/a")
        log(f"Status: Published ✅  |  Blog ID: {result.get('id', 'unknown')}")
    except Exception as exc:
        log(f"Source: {source_label}")
        log(f"Title: \"{title}\"")
        log(f"Status: FAILED — {exc}")
        draft_path = save_draft(title, body_html)
        log(f"Draft saved to: {draft_path}")

    # Mark Notion idea as used
    if notion_idea_used:
        try:
            mark_notion_idea_used(notion, notion_idea_used["id"])
            log(f"Notion idea marked as used: {notion_idea_used.get('idea', '')}")
        except Exception as exc:
            log(f"Failed to mark Notion idea as used: {exc}")


if __name__ == "__main__":
    main()
