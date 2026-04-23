from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from src import config

_client: WebClient | None = None


def _get_client() -> WebClient:
    global _client
    if _client is None:
        _client = WebClient(token=config.SLACK_BOT_TOKEN)
    return _client


def post_to_slack(channel: str, message: str) -> bool:
    try:
        response = _get_client().chat_postMessage(channel=channel, text=message)
        return bool(response.get("ok"))
    except SlackApiError as e:
        print(f"[slack] Error posting to #{channel}: {e.response['error']}")
        return False
