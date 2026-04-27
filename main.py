from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from src import config
from src.daily_digest import run_daily_digest


def scheduled_digest() -> None:
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Running daily digest...")
    try:
        run_daily_digest()
    except Exception as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ERROR: {e}")


if __name__ == "__main__":
    print("Social listening agent starting.")
    print(f"Topics  : {config.TOPICS}")
    print(f"Channel : #{config.SLACK_CHANNEL_NAME}")
    print(f"Schedule: daily at {config.DAILY_DIGEST_HOUR:02d}:00 IST")
    print(f"LinkedIn: {'enabled' if config.SERPAPI_KEY else 'disabled (no SERPAPI_KEY)'}")
    print(f"Twitter : {'enabled' if config.TWITTER_BEARER_TOKEN else 'disabled (no TWITTER_BEARER_TOKEN)'}")
    print("-" * 60)

    scheduler = BlockingScheduler(timezone="Asia/Kolkata")
    scheduler.add_job(
        scheduled_digest,
        CronTrigger(hour=config.DAILY_DIGEST_HOUR, minute=0, timezone="Asia/Kolkata"),
    )

    print(f"Next digest at {config.DAILY_DIGEST_HOUR:02d}:00 IST. Press Ctrl+C to stop.\n")

    try:
        scheduler.start()
    except KeyboardInterrupt:
        print("\nAgent stopped.")
