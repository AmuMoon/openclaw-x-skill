"""Thread creation, naming, continuation, and history tracking."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

CONFIG_DIR = Path.home() / ".config" / "openclaw-x"
HISTORY_FILE = CONFIG_DIR / "thread-history.json"


class ThreadManager:
    """Manage tweet threads with named tracking and history."""

    def __init__(self, history_path: Path | None = None) -> None:
        self.history_path = history_path or HISTORY_FILE

    def _ensure_dir(self) -> None:
        self.history_path.parent.mkdir(parents=True, exist_ok=True)

    def load_history(self) -> dict[str, Any]:
        """Load history from disk, or return empty structure."""
        if self.history_path.exists():
            with open(self.history_path, encoding="utf-8") as f:
                return json.load(f)
        return {"tweets": [], "threads": {}}

    def save_history(self, history: dict[str, Any]) -> None:
        """Persist history to disk."""
        self._ensure_dir()
        with open(self.history_path, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)

    def record_tweet(
        self,
        tweet_id: str,
        text: str,
        thread_name: str | None = None,
        parent_id: str | None = None,
    ) -> None:
        """Record a tweet to history. Keeps the last 100 entries."""
        history = self.load_history()
        entry = {
            "id": tweet_id,
            "text": text[:100] + ("..." if len(text) > 100 else ""),
            "timestamp": datetime.now().isoformat(),
            "threadName": thread_name,
            "parentId": parent_id,
        }
        history["tweets"].insert(0, entry)
        history["tweets"] = history["tweets"][:100]

        if thread_name:
            first_tweet_id = (
                history["threads"].get(thread_name, {}).get("firstTweetId", tweet_id)
            )
            history["threads"][thread_name] = {
                "latestTweetId": tweet_id,
                "firstTweetId": first_tweet_id,
                "updatedAt": datetime.now().isoformat(),
            }

        self.save_history(history)

    def get_thread_latest_id(self, thread_name: str) -> str:
        """Get the latest tweet ID from a named thread."""
        history = self.load_history()
        thread = history.get("threads", {}).get(thread_name)
        if not thread:
            raise ValueError(
                f'Thread "{thread_name}" not found. '
                "Use 'thread list' to see available threads."
            )
        return thread["latestTweetId"]

    def get_thread_info(self, thread_name: str) -> dict[str, Any]:
        """Get full info for a named thread."""
        history = self.load_history()
        thread = history.get("threads", {}).get(thread_name)
        if not thread:
            raise ValueError(f'Thread "{thread_name}" not found.')
        return {"name": thread_name, **thread}

    def list_threads(self) -> dict[str, dict[str, Any]]:
        """Return all named threads."""
        history = self.load_history()
        return history.get("threads", {})

    def get_recent_tweets(self, count: int = 10) -> list[dict[str, Any]]:
        """Return the N most recent tweets from history."""
        history = self.load_history()
        return history["tweets"][:count]

    def get_thread_tweets(self, thread_name: str) -> list[dict[str, Any]]:
        """Return all tweets belonging to a named thread, in chronological order."""
        history = self.load_history()
        if thread_name not in history.get("threads", {}):
            raise ValueError(f'Thread "{thread_name}" not found.')
        tweets = [t for t in history["tweets"] if t.get("threadName") == thread_name]
        tweets.reverse()  # chronological order (history is newest-first)
        return tweets
