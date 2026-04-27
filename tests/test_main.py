import os
import sys
import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from apscheduler.triggers.cron import CronTrigger

os.environ.setdefault("ANTHROPIC_API_KEY", "test-anthropic")
os.environ.setdefault("TWITTER_BEARER_TOKEN", "test-twitter")
os.environ.setdefault("SLACK_BOT_TOKEN", "test-slack")

for module_name in ["main", "src.agent", "src.config"]:
    sys.modules.pop(module_name, None)

import main


class MainTests(unittest.TestCase):
    def test_build_daily_trigger_uses_configured_ist_hour(self) -> None:
        main.config.DAILY_DIGEST_HOUR = 9
        main.config.DAILY_DIGEST_MINUTE = 0
        main.config.TIMEZONE = "Asia/Kolkata"

        trigger = main.build_daily_trigger()

        self.assertIsInstance(trigger, CronTrigger)
        next_run = trigger.get_next_fire_time(
            None,
            datetime(2026, 4, 27, 8, 59, tzinfo=ZoneInfo("Asia/Kolkata")),
        )
        self.assertEqual(next_run, datetime(2026, 4, 27, 9, 0, tzinfo=ZoneInfo("Asia/Kolkata")))


if __name__ == "__main__":
    unittest.main()
