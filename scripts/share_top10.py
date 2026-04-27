"""
One-shot runner: fetch today's top 10 posts and post to Slack.

Usage:
    python scripts/share_top10.py

Requires SERPAPI_KEY, SLACK_BOT_TOKEN, ANTHROPIC_API_KEY in .env
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from src.daily_digest import run_daily_digest

if __name__ == "__main__":
    run_daily_digest()
