from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger

from src import config
from src.agent import run_agent


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
    print(f"Sweep interval: every {config.SEARCH_INTERVAL_MINUTES} minutes")
    print(f"LinkedIn: {'enabled (SerpAPI configured)' if config.SERPAPI_KEY else 'disabled (no SERPAPI_KEY)'}")
    print("-" * 60)

    scheduler = BlockingScheduler()
    scheduler.add_job(
        scheduled_run,
        IntervalTrigger(minutes=config.SEARCH_INTERVAL_MINUTES),
        next_run_time=datetime.now(),  # run immediately on start
    )

    try:
        scheduler.start()
    except KeyboardInterrupt:
        print("\nAgent stopped.")
