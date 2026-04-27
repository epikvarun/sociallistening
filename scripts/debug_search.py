"""
Debug script — run this to see exactly what each search returns.

Usage:
    .venv/bin/python scripts/debug_search.py
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from src import config
from src.tools import linkedin, reddit

print("=== CONFIG CHECK ===")
print(f"SERPAPI_KEY   : {'set (' + config.SERPAPI_KEY[:8] + '...)' if config.SERPAPI_KEY else 'MISSING'}")
print(f"SLACK_TOKEN   : {'set' if config.SLACK_BOT_TOKEN else 'MISSING'}")
print(f"ANTHROPIC_KEY : {'set (' + config.ANTHROPIC_API_KEY[:12] + '...)' if config.ANTHROPIC_API_KEY else 'MISSING'}")
print()

TOPICS = ["Pronto", "Snabbit", "maid service", "home cleaning", "robo vacuum"]

print("=== LINKEDIN (SerpAPI) ===")
for topic in TOPICS:
    result = linkedin.search_linkedin(topic, max_results=3)
    if "error" in result:
        print(f"  [{topic}] ERROR: {result['error']}")
    else:
        posts = result.get("posts", [])
        print(f"  [{topic}] {len(posts)} posts found")
        for p in posts:
            print(f"    - {p['url']}")

print()
print("=== REDDIT ===")
for topic in TOPICS[:2]:
    result = reddit.search_reddit(topic, max_results=3)
    if "error" in result:
        print(f"  [{topic}] ERROR: {result['error']}")
    else:
        posts = result.get("posts", [])
        print(f"  [{topic}] {len(posts)} posts found")
        for p in posts:
            print(f"    - {p['url']}")
