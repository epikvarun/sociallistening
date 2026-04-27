import tweepy
from src import config


_client: tweepy.Client | None = None


def _get_client() -> tweepy.Client:
    global _client
    if _client is None:
        _client = tweepy.Client(bearer_token=config.TWITTER_BEARER_TOKEN, wait_on_rate_limit=False)
    return _client


def search_twitter(query: str, max_results: int = 20) -> dict:
    full_query = f"{query} (Gurgaon OR Gurugram OR Bangalore OR Bengaluru OR India) -is:retweet lang:en place_country:IN"
    max_results = max(10, min(max_results, 100))

    if config.DEBUG_MODE:
        print(f"[twitter/debug] Query: {full_query}")

    try:
        response = _get_client().search_recent_tweets(
            query=full_query,
            max_results=max_results,
            tweet_fields=["author_id", "created_at", "text"],
            expansions=["author_id"],
            user_fields=["username"],
        )
    except tweepy.TooManyRequests:
        return {"error": "rate_limited", "posts": []}
    except tweepy.Unauthorized:
        return {"error": "invalid_bearer_token", "posts": []}
    except Exception as e:
        return {"error": str(e), "posts": []}

    if config.DEBUG_MODE:
        print(f"[twitter/debug] Response data count: {len(response.data) if response.data else 0}")

    if not response.data:
        return {"posts": []}

    # Build username lookup from includes
    users = {}
    if response.includes and "users" in response.includes:
        for user in response.includes["users"]:
            users[user.id] = user.username

    posts = []
    for tweet in response.data:
        author = users.get(tweet.author_id, "unknown")
        posts.append({
            "url": f"https://twitter.com/i/web/status/{tweet.id}",
            "text": tweet.text,
            "author": f"@{author}",
            "platform": "twitter",
        })

    return {"posts": posts}
