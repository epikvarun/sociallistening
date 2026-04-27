import importlib
import os
import sys
import runpy
import unittest
from unittest import mock


def _load_agent():
    os.environ["ANTHROPIC_API_KEY"] = "test-anthropic"
    os.environ["TWITTER_BEARER_TOKEN"] = "test-twitter"
    os.environ["SLACK_BOT_TOKEN"] = "test-slack"

    for module_name in ["src.agent", "src.config"]:
        sys.modules.pop(module_name, None)

    return importlib.import_module("src.agent")


class FakeResponse:
    def __init__(self, stop_reason: str, content: list[object]):
        self.stop_reason = stop_reason
        self.content = content


class FakeToolUse:
    type = "tool_use"
    name = "post_to_slack"
    input = {
        "message": (
            "[Reddit] topic: `maids`\n"
            "> post\n"
            "https://example.com/1\n"
            "Epik's take: \"done\""
        )
    }
    id = "toolu_1"


class FakeMessages:
    def __init__(self) -> None:
        self.calls = 0

    def create(self, **kwargs):
        self.calls += 1
        return FakeResponse("tool_use", [FakeToolUse()])


class AgentTests(unittest.TestCase):
    def test_share_top10_script_invokes_limited_run(self) -> None:
        _load_agent()
        with mock.patch("src.agent.run_agent") as run_agent:
            runpy.run_path("scripts/share_top10.py", run_name="__main__")

        run_agent.assert_called_once_with(post_limit=10)

    def test_run_agent_stops_after_post_limit(self) -> None:
        agent = _load_agent()
        posted_messages: list[str] = []

        fake_messages = FakeMessages()
        with (
            mock.patch.object(agent._anthropic, "messages", fake_messages),
            mock.patch.object(
                agent.slack,
                "post_to_slack",
                lambda channel, message: posted_messages.append(message) or True,
            ),
            mock.patch.object(agent.deduplication, "mark_seen", lambda url: None),
            mock.patch.object(agent.excel_logger, "append_post", lambda message: None),
        ):
            posted_count = agent.run_agent(post_limit=1)

        self.assertEqual(fake_messages.calls, 1)
        self.assertEqual(posted_count, 1)
        self.assertEqual(posted_messages, [FakeToolUse.input["message"]])

    def test_run_agent_continues_without_limit(self) -> None:
        agent = _load_agent()

        class EndTurnMessages:
            def __init__(self) -> None:
                self.calls = 0

            def create(self, **kwargs):
                self.calls += 1
                return FakeResponse("end_turn", [])

        fake_messages = EndTurnMessages()
        with mock.patch.object(agent._anthropic, "messages", fake_messages):
            posted_count = agent.run_agent()

        self.assertEqual(fake_messages.calls, 1)
        self.assertEqual(posted_count, 0)


if __name__ == "__main__":
    unittest.main()
