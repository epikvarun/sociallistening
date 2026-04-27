import os
import requests
from src import config

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")


def post_to_slack(channel: str, message: str) -> bool:
    # Prefer webhook (simpler, no token rotation issues)
    if SLACK_WEBHOOK_URL:
        try:
            resp = requests.post(SLACK_WEBHOOK_URL, json={"text": message}, timeout=10)
            if resp.status_code == 200:
                return True
            print(f"[slack] Webhook error: {resp.status_code} {resp.text}")
            return False
        except Exception as e:
            print(f"[slack] Webhook exception: {e}")
            return False

    # Fallback to bot token
    try:
        from slack_sdk import WebClient
        from slack_sdk.errors import SlackApiError
        client = WebClient(token=config.SLACK_BOT_TOKEN)
        response = client.chat_postMessage(channel=channel, text=message)
        return bool(response.get("ok"))
    except Exception as e:
        print(f"[slack] Error posting to #{channel}: {e}")
        return False
