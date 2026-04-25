import os
from dotenv import load_dotenv

load_dotenv()

def _require(key: str) -> str:
    val = os.getenv(key, "").strip()
    if not val:
        raise ValueError(f"Missing required environment variable: {key}")
    return val

ANTHROPIC_API_KEY = _require("ANTHROPIC_API_KEY")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN", "").strip()
SLACK_BOT_TOKEN = _require("SLACK_BOT_TOKEN")
SLACK_CHANNEL_NAME = os.getenv("SLACK_CHANNEL_NAME", "social-listening")

# Optional — LinkedIn sweep is skipped if not set
SERPAPI_KEY = os.getenv("SERPAPI_KEY", "").strip()

SEARCH_INTERVAL_MINUTES = int(os.getenv("SEARCH_INTERVAL_MINUTES", "60"))
TWITTER_MAX_RESULTS = int(os.getenv("TWITTER_MAX_RESULTS", "20"))
LINKEDIN_MAX_RESULTS = int(os.getenv("LINKEDIN_MAX_RESULTS", "10"))
REDDIT_MAX_RESULTS = int(os.getenv("REDDIT_MAX_RESULTS", "10"))

TOPICS = [
    "maids",
    "cleaning",
    "robo vacuum",
    "Pronto",
    "Snabbit",
    "Meta Ray Ban projector",
    "IPL",
]

# Brands known to be India-based — skip location filtering for these
INDIA_NATIVE_BRANDS = {"Pronto", "Snabbit"}

# Location filter — only surface posts from these cities
TARGET_LOCATIONS = ["Gurgaon", "Gurugram", "Bangalore", "Bengaluru"]

# Indian subreddits to search alongside global search
INDIA_SUBREDDITS = "india+bangalore+gurgaon+delhi+mumbai+IndiaGaming+IndianGaming+indiasocial"

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "seen_posts.db")
