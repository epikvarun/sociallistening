"""
One-shot script: fetch top 10 LinkedIn posts across cleaning/home-services topics
and post each link to Slack + log to Excel.

Usage:
    python scripts/share_top10.py

Requires SERPAPI_KEY, SLACK_BOT_TOKEN, and ANTHROPIC_API_KEY in .env
"""

import os
import sys

# Allow imports from project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

import anthropic
from src import config
from src.tools import linkedin, slack, excel_logger

SEARCH_TOPICS = [
    ("Pronto", True),        # India-native brand — no location suffix
    ("Snabbit", True),       # India-native brand — no location suffix
    ("maid service", False),
    ("home cleaning", False),
    ("robo vacuum", False),
]

RESULTS_PER_TOPIC = 4   # over-fetch per topic so dedup still yields 10 total
TOP_N = 10

SLACK_CHANNEL = config.SLACK_CHANNEL_NAME

_anthropic = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)


def _epik_take(post_text: str, topic: str) -> str:
    prompt = (
        f"Topic: {topic}\n"
        f"Post snippet: {post_text[:300]}\n\n"
        "Write a single Epik brand comment (max 120 chars). "
        "Dry wit, no exclamation marks, no 'amazing'/'incredible'. "
        "Think clever brand reply energy."
    )
    msg = _anthropic.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=80,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text.strip().strip('"')


def _collect_posts() -> list[dict]:
    seen_urls: set[str] = set()
    collected: list[dict] = []

    for topic, is_native in SEARCH_TOPICS:
        if len(collected) >= TOP_N:
            break

        print(f"  Searching LinkedIn: {topic!r} ...")
        result = linkedin.search_linkedin(topic, max_results=RESULTS_PER_TOPIC)

        if "error" in result:
            print(f"    Skipped ({result['error']})")
            continue

        for post in result.get("posts", []):
            url = post.get("url", "")
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            collected.append({"topic": topic, **post})

        print(f"    Found {len(result.get('posts', []))} posts, running total: {len(collected)}")

    return collected[:TOP_N]


def _format_message(post: dict, take: str) -> str:
    text_preview = post.get("text", "")[:280]
    return (
        f"[LinkedIn] topic: `{post['topic']}`\n"
        f"> {text_preview}\n"
        f"{post['url']}\n"
        f'Epik\'s take: "{take}"'
    )


def main() -> None:
    if not config.SERPAPI_KEY:
        print("ERROR: SERPAPI_KEY not set — LinkedIn search is unavailable.")
        sys.exit(1)

    print(f"\nFetching top {TOP_N} LinkedIn posts across: "
          f"{', '.join(t for t, _ in SEARCH_TOPICS)}\n")

    posts = _collect_posts()

    if not posts:
        print("No LinkedIn posts found. Check your SERPAPI_KEY.")
        sys.exit(0)

    print(f"\nPosting {len(posts)} links to #{SLACK_CHANNEL} ...\n")

    for i, post in enumerate(posts, start=1):
        take = _epik_take(post.get("text", ""), post["topic"])
        message = _format_message(post, take)

        success = slack.post_to_slack(SLACK_CHANNEL, message)
        status = "OK" if success else "FAILED"
        print(f"  [{i:02d}/{len(posts)}] {status}  {post['url']}")

        if success:
            excel_logger.append_post(message)

    print(f"\nDone. Excel log: {excel_logger.EXCEL_PATH}")


if __name__ == "__main__":
    main()
