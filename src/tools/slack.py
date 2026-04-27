import requests
from src import config


def post_to_slack(channel: str, message: str) -> bool:
    """Post a message to Slack via incoming webhook."""
    try:
        response = requests.post(
            config.SLACK_WEBHOOK_URL,
            json={"text": message},
            timeout=10,
        )
        if response.status_code == 200 and response.text == "ok":
            return True
        print(f"[slack] Webhook error: {response.status_code} - {response.text}")
        return False
    except requests.RequestException as e:
        print(f"[slack] Request failed: {e}")
        return False
