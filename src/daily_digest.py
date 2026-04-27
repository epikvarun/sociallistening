"""
Daily digest: fetches top 10 posts across LinkedIn, Reddit, and Twitter
for the configured topics, posts each to Slack with a ready-to-paste comment,
and appends all rows to the Excel log.
"""

import anthropic
from datetime import datetime

from src import config
from src.tools import linkedin, reddit, twitter, slack, excel_logger

SEARCH_TOPICS = [
    ("Pronto", True),
    ("Snabbit", True),
    ("maid service", False),
    ("home cleaning", False),
    ("robo vacuum", False),
]

TOP_N = 10
PER_TOPIC = 4  # over-fetch per topic; dedup trims to TOP_N

_anthropic = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)


def _epik_take(post_text: str, topic: str) -> str:
    msg = _anthropic.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=80,
        messages=[{
            "role": "user",
            "content": (
                f"Topic: {topic}\n"
                f"Post: {post_text[:300]}\n\n"
                "Write one Epik brand reply (max 120 chars). "
                "Dry wit, no exclamation marks, no 'amazing'/'incredible'. "
                "Sounds like a clever brand account reply."
            ),
        }],
    )
    return msg.content[0].text.strip().strip('"')


def _collect_posts() -> list[dict]:
    seen: set[str] = set()
    posts: list[dict] = []

    for topic, is_native in SEARCH_TOPICS:
        if len(posts) >= TOP_N:
            break

        # LinkedIn
        if config.SERPAPI_KEY:
            result = linkedin.search_linkedin(topic, max_results=PER_TOPIC)
            for p in result.get("posts", []):
                url = p.get("url", "")
                if url and url not in seen:
                    seen.add(url)
                    posts.append({"topic": topic, **p})

        if len(posts) >= TOP_N:
            break

        # Reddit
        result = reddit.search_reddit(topic, max_results=PER_TOPIC)
        for p in result.get("posts", []):
            url = p.get("url", "")
            if url and url not in seen:
                seen.add(url)
                posts.append({"topic": topic, **p})

        if len(posts) >= TOP_N:
            break

        # Twitter (only if token configured)
        if config.TWITTER_BEARER_TOKEN:
            result = twitter.search_twitter(topic, max_results=PER_TOPIC)
            for p in result.get("posts", []):
                url = p.get("url", "")
                if url and url not in seen:
                    seen.add(url)
                    posts.append({"topic": topic, **p})

    return posts[:TOP_N]


def _format_post_message(index: int, total: int, post: dict, take: str) -> str:
    platform = post.get("platform", "linkedin").capitalize()
    topic = post["topic"]
    text = post.get("text", "")[:280]
    url = post.get("url", "")
    author = post.get("author", "")
    author_line = f"_{author}_\n" if author else ""

    return (
        f"*[{index}/{total}] {platform} · `{topic}`*\n"
        f"{author_line}"
        f"> {text}\n\n"
        f"🔗 *Post link:* {url}\n\n"
        f"💬 *Your comment — copy & paste on the post above:*\n"
        f'`{take}`'
    )


def run_daily_digest() -> None:
    channel = config.SLACK_CHANNEL_NAME
    date_str = datetime.now().strftime("%a, %d %b %Y")
    topics_str = " • ".join(t for t, _ in SEARCH_TOPICS)

    # Header
    slack.post_to_slack(channel, (
        f"📋 *Daily Social Digest — {date_str}*\n"
        f"Scanning: {topics_str}\n"
        f"{'─' * 40}"
    ))

    print(f"[digest] Collecting posts for: {topics_str}")
    posts = _collect_posts()

    if not posts:
        slack.post_to_slack(channel, "⚠️ No posts found today. Check API keys.")
        print("[digest] No posts found.")
        return

    print(f"[digest] Found {len(posts)} posts. Posting to #{channel} ...")

    for i, post in enumerate(posts, start=1):
        take = _epik_take(post.get("text", ""), post["topic"])
        message = _format_post_message(i, len(posts), post, take)

        success = slack.post_to_slack(channel, message)
        status = "OK" if success else "FAILED"
        print(f"  [{i:02d}/{len(posts)}] {status}  {post['url']}")

        if success:
            excel_logger.append_post(message)

    # Footer
    slack.post_to_slack(channel, (
        f"✅ *{len(posts)} posts above are ready for your comments.*\n"
        f"Open each 🔗 link → paste the 💬 comment → hit post."
    ))

    print(f"[digest] Done. Excel: {excel_logger.EXCEL_PATH}")
