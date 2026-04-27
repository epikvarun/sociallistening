from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from src import config
from src.agent import run_agent


def build_daily_trigger() -> CronTrigger:
    return CronTrigger(
        hour=config.DAILY_DIGEST_HOUR,
        minute=config.DAILY_DIGEST_MINUTE,
        timezone=config.TIMEZONE,
    )


def scheduled_run() -> None:
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting social listening sweep...")
    try:
        run_agent()
    except Exception as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ERROR during sweep: {e}")


if __name__ == "__main__":
    print(f"Social listening agent starting.")
    print(f"Topics: {config.TOPICS}")
    print(f"Slack channel: #{config.SLACK_CHANNEL_NAME}")
    print(
        "Daily digest: "
        f"{config.DAILY_DIGEST_HOUR:02d}:{config.DAILY_DIGEST_MINUTE:02d} "
        f"{config.TIMEZONE}"
    )
    print(f"LinkedIn: {'enabled (SerpAPI configured)' if config.SERPAPI_KEY else 'disabled (no SERPAPI_KEY)'}")
    print("-" * 60)

    scheduler = BlockingScheduler()
    scheduler.add_job(
        scheduled_run,
        build_daily_trigger(),
    )

    try:
        scheduler.start()
    except KeyboardInterrupt:
        print("\nAgent stopped.")
