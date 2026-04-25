import requests
from src import config

SERPAPI_URL = "https://serpapi.com/search.json"


def search_linkedin(query: str, max_results: int = 10) -> dict:
    if not config.SERPAPI_KEY:
        return {"error": "no_serpapi_key", "posts": [], "note": "Set SERPAPI_KEY to enable LinkedIn search"}

    india_native = query in getattr(config, "INDIA_NATIVE_BRANDS", set())
    location_hint = "" if india_native else " (India OR Gurgaon OR Bangalore OR Bengaluru)"
    params = {
        "engine": "google",
        "q": f'site:linkedin.com/posts "{query}"{location_hint} -intitle:jobs',
        "api_key": config.SERPAPI_KEY,
        "num": max_results,
    }

    try:
        resp = requests.get(SERPAPI_URL, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.Timeout:
        return {"error": "timeout", "posts": []}
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "posts": []}

    if "error" in data:
        return {"error": data["error"], "posts": []}

    organic = data.get("organic_results", [])
    posts = []
    for item in organic[:max_results]:
        posts.append({
            "url": item.get("link", ""),
            "text": item.get("snippet", item.get("title", "")),
            "author": "",
            "platform": "linkedin",
        })

    return {"posts": posts}
