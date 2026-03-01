"""Tests for openclaw_x.threads."""

from __future__ import annotations

import pytest

from openclaw_x.threads import ThreadManager


@pytest.fixture
def thread_mgr(tmp_path):
    """ThreadManager with a temp history file."""
    return ThreadManager(history_path=tmp_path / "history.json")


class TestThreadManager:
    def test_load_empty_history(self, thread_mgr):
        history = thread_mgr.load_history()
        assert history == {"tweets": [], "threads": {}}

    def test_record_tweet(self, thread_mgr):
        thread_mgr.record_tweet("111", "Hello world")
        history = thread_mgr.load_history()
        assert len(history["tweets"]) == 1
        assert history["tweets"][0]["id"] == "111"
        assert history["tweets"][0]["text"] == "Hello world"

    def test_record_tweet_truncates_text(self, thread_mgr):
        long_text = "x" * 200
        thread_mgr.record_tweet("222", long_text)
        history = thread_mgr.load_history()
        assert history["tweets"][0]["text"].endswith("...")
        assert len(history["tweets"][0]["text"]) == 103  # 100 chars + "..."

    def test_record_with_thread_name(self, thread_mgr):
        thread_mgr.record_tweet("333", "First", thread_name="mythread")
        history = thread_mgr.load_history()
        assert "mythread" in history["threads"]
        assert history["threads"]["mythread"]["firstTweetId"] == "333"
        assert history["threads"]["mythread"]["latestTweetId"] == "333"

    def test_record_continues_thread(self, thread_mgr):
        thread_mgr.record_tweet("100", "First", thread_name="t1")
        thread_mgr.record_tweet("101", "Second", thread_name="t1", parent_id="100")
        history = thread_mgr.load_history()
        assert history["threads"]["t1"]["firstTweetId"] == "100"
        assert history["threads"]["t1"]["latestTweetId"] == "101"

    def test_history_max_100(self, thread_mgr):
        for i in range(110):
            thread_mgr.record_tweet(str(i), f"Tweet {i}")
        history = thread_mgr.load_history()
        assert len(history["tweets"]) == 100

    def test_get_thread_latest_id(self, thread_mgr):
        thread_mgr.record_tweet("500", "First", thread_name="demo")
        thread_mgr.record_tweet("501", "Second", thread_name="demo", parent_id="500")
        assert thread_mgr.get_thread_latest_id("demo") == "501"

    def test_get_thread_latest_id_not_found(self, thread_mgr):
        with pytest.raises(ValueError, match="not found"):
            thread_mgr.get_thread_latest_id("nonexistent")

    def test_list_threads(self, thread_mgr):
        thread_mgr.record_tweet("1", "A", thread_name="alpha")
        thread_mgr.record_tweet("2", "B", thread_name="beta")
        threads = thread_mgr.list_threads()
        assert "alpha" in threads
        assert "beta" in threads

    def test_get_recent_tweets(self, thread_mgr):
        thread_mgr.record_tweet("10", "A")
        thread_mgr.record_tweet("20", "B")
        thread_mgr.record_tweet("30", "C")
        recent = thread_mgr.get_recent_tweets(2)
        assert len(recent) == 2
        assert recent[0]["id"] == "30"  # most recent first

    def test_get_thread_tweets(self, thread_mgr):
        thread_mgr.record_tweet("1", "Solo tweet")
        thread_mgr.record_tweet("2", "Thread first", thread_name="t")
        thread_mgr.record_tweet("3", "Thread second", thread_name="t", parent_id="2")
        tweets = thread_mgr.get_thread_tweets("t")
        assert len(tweets) == 2
        assert tweets[0]["id"] == "2"  # chronological order
        assert tweets[1]["id"] == "3"

    def test_get_thread_tweets_not_found(self, thread_mgr):
        with pytest.raises(ValueError, match="not found"):
            thread_mgr.get_thread_tweets("nope")

    def test_get_thread_info(self, thread_mgr):
        thread_mgr.record_tweet("1", "First", thread_name="info_test")
        info = thread_mgr.get_thread_info("info_test")
        assert info["name"] == "info_test"
        assert info["firstTweetId"] == "1"

    def test_persistence(self, thread_mgr):
        """Data survives creating a new ThreadManager with the same path."""
        thread_mgr.record_tweet("999", "Persist test", thread_name="persist")
        mgr2 = ThreadManager(history_path=thread_mgr.history_path)
        assert mgr2.get_thread_latest_id("persist") == "999"
