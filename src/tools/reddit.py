import json
import requests
from src import config

REDDIT_SEARCH_URL = "https://www.reddit.com/search.json"
REDDIT_SUBREDDIT_URL = "https://www.reddit.com/r/{subreddits}/search.json"

_HEADERS = {"User-Agent": "EpikSocialBot/1.0"}


def search_reddit(query: str, max_results: int = 10) -> dict:
    posts = []

    if config.DEBUG_MODE:
        print(f"[reddit/debug] Query: {query}, subreddits: {config.INDIA_SUBREDDITS}")

    # 1. Search within Indian subreddits first
    try:
        resp = requests.get(
            REDDIT_SUBREDDIT_URL.format(subreddits=config.INDIA_SUBREDDITS),
            params={"q": query, "sort": "new", "restrict_sr": "true", "limit": max_results},
            headers=_HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        if config.DEBUG_MODE:
            print(f"[reddit/debug] Subreddit search response:\n{json.dumps(data, indent=2)[:1500]}")
        for item in data.get("data", {}).get("children", []):
            d = item["data"]
            posts.append({
                "url": f"https://reddit.com{d['permalink']}",
                "text": f"{d['title']} — {d.get('selftext', '')[:300]}".strip(" —"),
                "author": f"u/{d['author']}",
                "subreddit": d["subreddit"],
                "platform": "reddit",
            })
    except Exception as e:
        return {"error": str(e), "posts": []}

    # 2. If not enough, also search globally but flag for agent to filter by India context
    if len(posts) < max_results:
        try:
            resp = requests.get(
                REDDIT_SEARCH_URL,
                params={"q": f"{query} india OR bangalore OR gurgaon", "sort": "new", "limit": max_results - len(posts)},
                headers=_HEADERS,
                timeout=15,
            )
            resp.raise_for_status()
            for item in resp.json().get("data", {}).get("children", []):
                d = item["data"]
                url = f"https://reddit.com{d['permalink']}"
                if not any(p["url"] == url for p in posts):
                    posts.append({
                        "url": url,
                        "text": f"{d['title']} — {d.get('selftext', '')[:300]}".strip(" —"),
                        "author": f"u/{d['author']}",
                        "subreddit": d["subreddit"],
                        "platform": "reddit",
                    })
        except Exception:
            pass

    return {"posts": posts}
