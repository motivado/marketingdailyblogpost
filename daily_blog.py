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

# ── Config ────────────────────────────────────────────────────────────────────────────────
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


# ── Helpers ─────────────────────────────────────────────────────────────────────────────
ndef today_str() -> str:
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


# ── Step 1: Notion — Newsletter Ideas (unused) ────────────────────────────────────────────
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


# ── Step 1: Notion — Instagram Ideas (not Posted) ──────────────────────────────────────────
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


# ── Step 2: RSS feed check ───────────────────────────────────────────────────────────────────
def fetch_new_posts(rss_url: str) -> list[dict]:
    """Return posts published today or yesterday."""
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    feed = feedparser.parse(rss_url)
    new = []
    for entry in feed.entries:
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


# ── Step 4: Write article from Instagram post ────────────────────────────────────────────────
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
        <p>Teachers and parents don&rsquo;t need a high-tech lab to create these moments. Open-ended challenges &mdash; even simple ones with cardboard, wheels, or basic electronics &mdash; put children in the driver&rsquo;s seat of their own learning. The goal is not a perfect result; it&rsquo;s the thinking along the way.</p>

        <h2>TokyLabs After-School Activities</h2>
        <p>TokyLabs brings exactly this energy into international schools across Bali. Our team of trained educators leads after-school robotics sessions where students work with Tokymaker kits to design, build, and program real devices. Every session is a new challenge, and every challenge builds the skills children will rely on for life.</p>
    """).strip()

    return title, body


# ── Step 5: Write article from Notion idea ───────────────────────────────────────────────────
def write_article_from_notion(idea: dict) -> tuple[str, str]:
    """Return (title, body_html) for a newsletter idea or Instagram idea topic."""
    topic = idea["idea"] if "idea" in idea else idea["name"]
    t = topic.lower()

    if "tokymini" in t or "screenless" in t or ("new" in t and "version" in t):
        title = "Why Screenless Robotics Is the Next Big Thing for Primary School Kids"
        body = textwrap.dedent("""
            <p>What if the most powerful learning tool for young children had no screen at all? In a world that often equates technology with screens, screenless robotics flips the script entirely &mdash; and it turns out, that is exactly what young learners need most.</p>

            <h2>Why Hands-On Matters More Than Ever</h2>

            <p>Primary school children &mdash; roughly ages 5 to 11 &mdash; are in a critical window for building the foundations of lifelong learning: fine motor control, spatial reasoning, cause-and-effect thinking, and early problem-solving. These skills do not grow by watching a video or tapping a tablet. They grow when children use their hands, make something move, take it apart, and figure out why it works the way it does.</p>

            <p>Screenless robotics kits are designed around this exact insight. Rather than asking young learners to stare at a screen and write lines of code, they invite children to connect pieces, flip switches, and watch physical reactions unfold in real time. The feedback is immediate and tangible &mdash; the robot moves, or it does not. That direct feedback loop is one of the most effective teaching mechanisms in early childhood education, and research consistently shows that tactile, physical learning experiences lead to deeper retention and stronger creative confidence.</p>

            <h2>Three Ways to Bring Screenless Robotics to Life at Home or in Class</h2>

            <p>For teachers and parents introducing robotics at the primary level, these three principles make all the difference:</p>

            <ul>
              <li><strong>Start with exploring, not explaining.</strong> Let children interact with the kit freely before introducing any instructions. Curiosity is the best teacher &mdash; and young children will naturally start experimenting the moment you hand them something new.</li>
              <li><strong>Treat every mistake as a milestone.</strong> When a circuit does not close or the robot goes in the wrong direction, that is not failure &mdash; that is the learning event. Celebrate the moment a child asks &ldquo;Why did that happen?&rdquo; rather than the moment they get it right.</li>
              <li><strong>Ask questions instead of giving answers.</strong> &ldquo;What do you think would happen if you moved this piece?&rdquo; or &ldquo;Can you think of another way?&rdquo; builds the habit of inquiry that will serve children across every subject and every stage of life.</li>
            </ul>

            <h2>Something Exciting Is Coming from TokyLabs</h2>

            <p>At TokyLabs, the belief that joy and hands-on creation belong together is at the heart of everything the team builds. Tokymini &mdash; the screenless robotics kit designed specifically for primary school children &mdash; brings these principles to life for the youngest makers. It is purposefully screen-free, tactile, and designed to spark curiosity from the very first moment a child opens the box. And there is exciting news ahead: a new version of Tokymini is on its way. More creative possibilities, the same joyful spirit. Head over to <a href=\"https://tokylabs.com\">tokylabs.com</a> to stay updated and be among the first to discover what is coming.</p>
        """).strip()

    elif "critical thinking" in t or "think" in t:
        title = "Why Critical Thinking Is the Most Important Skill You Can Give Your Child in the Age of AI"
        body = textwrap.dedent("""
            <p>Your child is growing up in a world where artificial intelligence can answer almost any question in seconds. But here is what AI still cannot do: <em>think for your child</em>. The real advantage in tomorrow&rsquo;s world is not having the right answers &mdash; it&rsquo;s knowing how to ask the right questions, evaluate information, and make thoughtful decisions. Critical thinking is not a bonus skill anymore. It is the foundation.</p>

            <h2>What Critical Thinking Really Means for Kids</h2>
            <p>Critical thinking is the ability to analyze a situation, weigh evidence, and reach a reasoned conclusion &mdash; rather than simply accepting the first answer that appears. For children, this looks like questioning why something works the way it does, testing ideas, making mistakes, and trying again. It is less about raw intelligence and more about <em>how</em> a child approaches a problem.</p>
            <p>Research consistently shows that children who develop critical thinking skills early become more confident decision-makers, stronger communicators, and more adaptable learners. The good news? These skills are not taught through lectures. They are built through <em>doing</em>.</p>

            <h2>How Hands-On Learning Builds Young Thinkers</h2>
            <p>When a child builds a robot &mdash; even a simple screenless one &mdash; they are not following a script. They set a goal, design a solution, test it, observe what goes wrong, and iterate. This process, repeated across dozens of small projects, is how critical thinking becomes a habit rather than a lesson.</p>
            <p>For teachers and parents, the key is to resist giving the answer. When a child&rsquo;s robot does not behave as expected, that moment of confusion is the learning. Ask questions instead: <em>What do you think went wrong? What could we try differently?</em> The struggle is the point.</p>

            <h2>Practical Ways to Nurture a Critical Thinker</h2>
            <ul>
            <li><strong>Introduce &ldquo;why&rdquo; conversations</strong> regularly &mdash; why does something work, what would happen if one thing changed?</li>
            <li><strong>Encourage low-stakes experimentation</strong>: building, cooking, gardening, or simple craft projects where children make decisions and observe outcomes.</li>
            <li><strong>Celebrate the curiosity to try again</strong> rather than the success itself &mdash; resilience and reflection are the real wins.</li>
            </ul>

            <h2>How TokyLabs Puts This Into Practice</h2>
            <p>At TokyLabs, building thinkers is at the heart of everything we do. Our Tokymini kits &mdash; screenless robotics designed for primary school children &mdash; remove the distraction of screens and focus entirely on physical interaction, cause-and-effect reasoning, and independent problem-solving. There are no step-by-step instructions to follow. Children explore, experiment, and figure things out with the support of trained mentors who know that the best answer is the one a child discovers on their own.</p>
        """).strip()

    elif "swarm" in t or "nasa" in t:
        title = "What NASA&rsquo;s Robot Swarms Can Teach Us About Educating Kids"
        body = textwrap.dedent("""
            <p>What if the best way to prepare children for the future was to let them solve real problems &mdash; the same kind engineers at NASA grapple with? It sounds ambitious, but the principle is simpler than you think.</p>

            <h2>The NASA Swarmathon: Real Students, Real Problems</h2>
            <p>NASA&rsquo;s Swarmathon is a competition where students design algorithms for swarms of small robots called Swarmies. These robots must coordinate to search an area efficiently &mdash; the same challenge faced by robots exploring distant planets. Students learn robotics, programming, and teamwork while solving a genuine, open-ended problem with no single correct answer.</p>
            <p>The results? Students who participate don&rsquo;t just learn code. They learn how to think like engineers: break a complex problem into parts, test hypotheses, collaborate under pressure, and adapt when things don&rsquo;t go as planned.</p>

            <h2>Bringing the Swarmathon Mindset to Any Classroom</h2>
            <p>You don&rsquo;t need a NASA budget to create this kind of learning. The key ingredients are: an open-ended challenge, the freedom to fail and iterate, and a teacher who asks questions rather than giving answers. A classroom robotics kit can replicate the same cognitive journey &mdash; setting goals, building a solution, watching it fail, and improving it.</p>

            <h2>TokyLabs Teacher Training</h2>
            <p>At TokyLabs, we believe every teacher can create this kind of environment &mdash; and we help them get there. Our STEM robotics certification programs give educators the confidence, tools, and techniques to facilitate open-ended challenges using Tokymaker in their own classrooms. Because when teachers shift from instructing to mentoring, the whole classroom transforms.</p>
        """).strip()

    elif "joy" in t or "philosophy" in t:
        title = "Joy Is Not Just a Feeling &mdash; It&rsquo;s the Engine of Real Learning"
        body = textwrap.dedent("""
            <p>When was the last time you watched a child completely lost in something they loved? No prompting, no reward &mdash; just pure, absorbed curiosity. That is joy at work. And it turns out, joy is not a side effect of good learning. It is the source of it.</p>

            <h2>Why Joy Makes Learning Stick</h2>
            <p>Neuroscience backs what great educators have always known: when children experience joy while learning, their brains form stronger, longer-lasting memories. The emotional engagement that comes from excitement and delight acts as a signal to the brain that says, &ldquo;this matters &mdash; remember it.&rdquo; Dry, passive instruction rarely produces this effect. Hands-on creation almost always does.</p>
            <p>Joy also builds resilience. A child who is genuinely enjoying a challenge will try again when something goes wrong &mdash; not because they were told to, but because they <em>want</em> to see it work. That intrinsic motivation is the foundation of lifelong learning.</p>

            <h2>Creating Joyful Learning Moments</h2>
            <p>Joy in learning does not require expensive equipment or elaborate setups. It requires giving children agency &mdash; the freedom to choose how they approach a problem, to make it their own, to surprise themselves with what they can do. For teachers, this means designing open-ended challenges rather than step-by-step instructions. For parents, it means following your child&rsquo;s curiosity rather than directing it.</p>
            <p>Even a simple question &mdash; &ldquo;What would happen if we changed this?&rdquo; &mdash; can transform a routine activity into a joyful experiment. The goal is not the finished product. It is the spark in a child&rsquo;s eyes when something clicks.</p>

            <h2>Joy at the Heart of TokyLabs</h2>
            <p>At TokyLabs, joy is not a teaching strategy. It is the whole philosophy. From Tokymini kits that let primary school children build and explore without ever looking at a screen, to Tokymaker sessions where older students design real devices from scratch, every experience is engineered to make children feel the thrill of creation. Because we believe that a child who learns with joy does not just learn better &mdash; they become someone who never stops wanting to learn.</p>
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


# ── Step 6: Publish to Selldone ────────────────────────────────────────────────────────────────────
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
    resp.raise_for_status()
    return resp.json()


# ── Step 7: Mark Notion idea as used ─────────────────────────────────────────────────────────────────────────────
def mark_notion_idea_used(notion: NotionClient, page_id: str) -> None:
    notion.pages.update(page_id=page_id, properties={"Used?": {"checkbox": True}})


# ── Main workflow ──────────────────────────────────────────────────────────────────────────────────────
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
            topic_idea = newsletter_ideas[0]
            notion_idea_used = topic_idea
            source_label = f"Notion Newsletter Idea ({topic_idea['section']})"
        else:
            log("No unused Notion ideas available. Skipping today.")
            return

        title, body_html = write_article_from_notion(topic_idea)

    # Step 6: Publish
    try:
        result = publish_to_selldone(title, body_html, image_url)
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
