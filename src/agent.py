import json
import re
import anthropic

from src import config, deduplication
from src.tools import twitter, linkedin, slack, reddit

_anthropic = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

SYSTEM_PROMPT = f"""You are the social listening agent for Epik — a punchy consumer tech startup that's millennial-nerdy and slightly self-aware. Think clever brand account energy, not corporate PR.

LOCATION RULE — strictly enforced:
- Only surface posts from people in Gurgaon, Gurugram, Bangalore, or Bengaluru (India).
- Discard any post that is clearly from the US, Europe, or an unknown global account with no India context.
- Signals of India context: mentions of Indian cities, Indian slang, Indian cricket references, Indian prices (₹), posting in IST, or the subreddit is India-focused.
- When in doubt, skip the post.

Your job each run:
1. For each topic, call search_twitter, search_reddit, and search_linkedin (if available).
2. For each post that passes the India/Gurgaon/Bangalore location filter, craft a short Epik brand comment (max 120 chars).
3. Call post_to_slack with a formatted message for each qualifying post.
4. If a search returns no results, an error, or only non-India posts, move to the next topic.
5. If a platform returns {{"error": "no_serpapi_key"}}, skip LinkedIn silently.

Epik voice rules:
- Sharp and short — 1-2 sentences max
- No exclamation marks. Never say "amazing", "incredible", "awesome"
- Dry wit, tech references, home/life puns welcome
- Write like a clever reply the brand account would leave on the post
- Examples: "Automation: 1. Domestic bliss: 0." / "Peak 2025: your floor cleaner has better route planning than your GPS."

Topics to sweep: {", ".join(config.TOPICS)}

Slack message format — always use exactly this structure:
```
[PLATFORM] topic: `<topic>`
> <first 280 chars of post text>
<post URL>
Epik's take: "<your comment>"
```
Replace PLATFORM with Twitter, Reddit, or LinkedIn. Keep it clean, no extra headers."""

TOOLS = [
    {
        "name": "search_twitter",
        "description": "Search Twitter/X for recent posts from India mentioning a topic. Returns new (not previously seen) posts only. Already filtered to India — you still must check for Gurgaon/Bangalore context.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search term or phrase"},
                "max_results": {"type": "integer", "description": "Max posts to return (10-100)", "default": 20},
            },
            "required": ["query"],
        },
    },
    {
        "name": "search_reddit",
        "description": "Search Indian subreddits (r/india, r/bangalore, r/gurgaon, etc.) for posts mentioning a topic. Returns new posts only.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search term or phrase"},
                "max_results": {"type": "integer", "description": "Max posts to return", "default": 10},
            },
            "required": ["query"],
        },
    },
    {
        "name": "search_linkedin",
        "description": "Search LinkedIn for public posts mentioning a topic via Google (SerpAPI). Returns new posts only. May return {\"error\": \"no_serpapi_key\"} if not configured.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search term or phrase"},
                "max_results": {"type": "integer", "description": "Max posts to return", "default": 10},
            },
            "required": ["query"],
        },
    },
    {
        "name": "post_to_slack",
        "description": "Post a formatted message to the Slack social-listening channel. Call this once per post, with the full formatted message including the Epik comment.",
        "input_schema": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "Fully formatted Slack message to post"},
            },
            "required": ["message"],
        },
    },
]


def _extract_urls(text: str) -> list[str]:
    return re.findall(r"https?://\S+", text)


def _dispatch(name: str, inputs: dict, seen_urls: set[str]) -> dict:
    if name == "search_twitter":
        result = twitter.search_twitter(
            inputs["query"], inputs.get("max_results", config.TWITTER_MAX_RESULTS)
        )
        if "posts" in result:
            new_posts = [p for p in result["posts"] if p["url"] not in seen_urls]
            filtered = len(result["posts"]) - len(new_posts)
            result["posts"] = new_posts
            if filtered:
                result["filtered_already_seen"] = filtered
        return result

    if name == "search_reddit":
        result = reddit.search_reddit(
            inputs["query"], inputs.get("max_results", config.REDDIT_MAX_RESULTS)
        )
        if "posts" in result:
            new_posts = [p for p in result["posts"] if p["url"] not in seen_urls]
            filtered = len(result["posts"]) - len(new_posts)
            result["posts"] = new_posts
            if filtered:
                result["filtered_already_seen"] = filtered
        return result

    if name == "search_linkedin":
        result = linkedin.search_linkedin(
            inputs["query"], inputs.get("max_results", config.LINKEDIN_MAX_RESULTS)
        )
        if "posts" in result:
            new_posts = [p for p in result["posts"] if p["url"] not in seen_urls]
            filtered = len(result["posts"]) - len(new_posts)
            result["posts"] = new_posts
            if filtered:
                result["filtered_already_seen"] = filtered
        return result

    if name == "post_to_slack":
        message = inputs["message"]
        success = slack.post_to_slack(config.SLACK_CHANNEL_NAME, message)
        if success:
            for url in _extract_urls(message):
                deduplication.mark_seen(url)
                seen_urls.add(url)
        return {"success": success}

    return {"error": f"unknown tool: {name}"}


def run_agent() -> None:
    seen_urls: set[str] = set()

    messages = [{"role": "user", "content": "Run the social listening sweep now across all topics. Remember: Gurgaon and Bangalore only."}]

    print(f"[agent] Starting sweep for topics: {config.TOPICS}")
    print(f"[agent] Location filter: {config.TARGET_LOCATIONS}")

    while True:
        response = _anthropic.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=8096,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            print("[agent] Sweep complete.")
            break

        if response.stop_reason != "tool_use":
            print(f"[agent] Unexpected stop_reason: {response.stop_reason}. Ending.")
            break

        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            print(f"[agent] Tool call: {block.name}({json.dumps(block.input)})")
            result = _dispatch(block.name, block.input, seen_urls)
            print(f"[agent] Tool result: {json.dumps(result)[:200]}")
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(result),
            })

        messages.append({"role": "user", "content": tool_results})
