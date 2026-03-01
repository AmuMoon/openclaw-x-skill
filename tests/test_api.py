"""Tests for openclaw_x.api."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest

from openclaw_x.api import XApiClient


@pytest.fixture
def client(creds):
    c = XApiClient(creds)
    yield c
    c.close()


class TestXApiClientHandle:
    def test_rate_limit_raises(self, client):
        resp = MagicMock(spec=httpx.Response)
        resp.status_code = 429
        resp.headers = {"x-rate-limit-reset": "1700000000"}
        with pytest.raises(RuntimeError, match="Rate limited"):
            client._handle(resp)

    def test_api_error_raises(self, client):
        resp = MagicMock(spec=httpx.Response)
        resp.status_code = 403
        resp.is_success = False
        resp.json.return_value = {"errors": [{"detail": "Forbidden"}]}
        resp.text = "Forbidden"
        with pytest.raises(RuntimeError, match="API error.*403.*Forbidden"):
            client._handle(resp)

    def test_success_returns_data(self, client):
        resp = MagicMock(spec=httpx.Response)
        resp.status_code = 200
        resp.is_success = True
        resp.json.return_value = {"data": {"id": "123"}}
        result = client._handle(resp)
        assert result["data"]["id"] == "123"


class TestPostTweet:
    def test_post_tweet_body(self, client):
        """Verify the JSON body structure for post_tweet."""
        with patch.object(client, "_oauth_request") as mock:
            mock.return_value = {"data": {"id": "1"}}
            client.post_tweet("Hello")
            mock.assert_called_once()
            _, _, body = mock.call_args[0]
            assert body == {"text": "Hello"}

    def test_post_tweet_with_reply(self, client):
        with patch.object(client, "_oauth_request") as mock:
            mock.return_value = {"data": {"id": "2"}}
            client.post_tweet("Reply", reply_to="999")
            body = mock.call_args[0][2]
            assert body["reply"] == {"in_reply_to_tweet_id": "999"}

    def test_post_tweet_with_media(self, client):
        with patch.object(client, "_oauth_request") as mock:
            mock.return_value = {"data": {"id": "3"}}
            client.post_tweet("With media", media_ids=["m1", "m2"])
            body = mock.call_args[0][2]
            assert body["media"] == {"media_ids": ["m1", "m2"]}

    def test_post_tweet_with_poll(self, client):
        with patch.object(client, "_oauth_request") as mock:
            mock.return_value = {"data": {"id": "4"}}
            client.post_tweet("Poll", poll_options=["A", "B"])
            body = mock.call_args[0][2]
            assert body["poll"]["options"] == ["A", "B"]

    def test_post_tweet_with_quote(self, client):
        with patch.object(client, "_oauth_request") as mock:
            mock.return_value = {"data": {"id": "5"}}
            client.post_tweet("Quoting", quote_tweet_id="777")
            body = mock.call_args[0][2]
            assert body["quote_tweet_id"] == "777"


class TestGetAuthenticatedUserId:
    def test_caches_user_id(self, client):
        with patch.object(client, "_oauth_request") as mock:
            mock.return_value = {"data": {"id": "42"}}
            uid1 = client.get_authenticated_user_id()
            uid2 = client.get_authenticated_user_id()
            assert uid1 == uid2 == "42"
            mock.assert_called_once()  # cached after first call


class TestSearchTweets:
    def test_clamps_max_results(self, client):
        with patch.object(client._http, "get") as mock_get:
            resp = MagicMock(spec=httpx.Response)
            resp.status_code = 200
            resp.is_success = True
            resp.json.return_value = {"data": []}
            mock_get.return_value = resp
            client.search_tweets("test", max_results=5)
            call_params = mock_get.call_args
            assert call_params.kwargs["params"]["max_results"] == "10"  # clamped to min 10
