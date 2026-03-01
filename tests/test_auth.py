"""Tests for openclaw_x.auth."""

from __future__ import annotations

import re

from openclaw_x.auth import generate_oauth_header


class TestGenerateOAuthHeader:
    def test_returns_oauth_prefix(self, creds):
        header = generate_oauth_header("GET", "https://api.x.com/2/tweets/123", creds)
        assert header.startswith("OAuth ")

    def test_contains_consumer_key(self, creds):
        header = generate_oauth_header("GET", "https://api.x.com/2/tweets/123", creds)
        assert "oauth_consumer_key" in header
        assert "test_key" in header

    def test_contains_signature(self, creds):
        header = generate_oauth_header("POST", "https://api.x.com/2/tweets", creds)
        assert "oauth_signature=" in header

    def test_contains_token(self, creds):
        header = generate_oauth_header("GET", "https://api.x.com/2/users/me", creds)
        assert "oauth_token" in header
        assert "test_token" in header

    def test_different_urls_different_signatures(self, creds):
        h1 = generate_oauth_header("GET", "https://api.x.com/2/tweets/1", creds)
        h2 = generate_oauth_header("GET", "https://api.x.com/2/tweets/2", creds)
        sig1 = re.search(r'oauth_signature="([^"]+)"', h1).group(1)
        sig2 = re.search(r'oauth_signature="([^"]+)"', h2).group(1)
        assert sig1 != sig2

    def test_url_with_query_params(self, creds):
        url = "https://api.x.com/2/tweets/123?tweet.fields=created_at,public_metrics"
        header = generate_oauth_header("GET", url, creds)
        assert header.startswith("OAuth ")

    def test_with_extra_params(self, creds):
        header = generate_oauth_header(
            "POST",
            "https://api.x.com/2/tweets",
            creds,
            params={"status": "hello"},
        )
        assert header.startswith("OAuth ")
        assert "oauth_signature" in header
