from src.agent import run_agent


if __name__ == "__main__":
    print("Posting up to 10 qualifying social listening posts to Slack...")
    run_agent(post_limit=10)
