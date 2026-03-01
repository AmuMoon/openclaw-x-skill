"""Click CLI for openclaw-x."""

from __future__ import annotations

import json

import click

from . import __version__
from .api import XApiClient
from .auth import load_credentials
from .formatters import format_output
from .media import MediaUploader
from .threads import ThreadManager
from .utils import parse_tweet_id, strip_at


class State:
    def __init__(self, mode: str, verbose: bool = False) -> None:
        self.mode = mode
        self.verbose = verbose
        self._client: XApiClient | None = None
        self._uploader: MediaUploader | None = None
        self._threads: ThreadManager | None = None

    @property
    def client(self) -> XApiClient:
        if self._client is None:
            creds = load_credentials()
            self._client = XApiClient(creds)
        return self._client

    @property
    def uploader(self) -> MediaUploader:
        if self._uploader is None:
            creds = load_credentials()
            self._uploader = MediaUploader(creds)
        return self._uploader

    @property
    def threads(self) -> ThreadManager:
        if self._threads is None:
            self._threads = ThreadManager()
        return self._threads

    def output(self, data, title: str = "") -> None:
        format_output(data, self.mode, title, verbose=self.verbose)

    def upload_media(self, media_path: str) -> str:
        """Upload media and return media_id."""
        return self.uploader.upload(media_path)

    def post_and_record(
        self,
        text: str,
        reply_to: str | None = None,
        quote_tweet_id: str | None = None,
        media_ids: list[str] | None = None,
        poll_options: list[str] | None = None,
        thread_name: str | None = None,
        parent_id: str | None = None,
    ) -> dict:
        """Post a tweet and record it in thread history."""
        data = self.client.post_tweet(
            text,
            reply_to=reply_to,
            quote_tweet_id=quote_tweet_id,
            media_ids=media_ids,
            poll_options=poll_options,
        )
        tweet_id = data["data"]["id"]
        self.threads.record_tweet(tweet_id, text, thread_name, parent_id)
        return data


pass_state = click.make_pass_decorator(State)


# ============================================================
# Root group
# ============================================================


@click.group()
@click.option("--json", "-j", "fmt", flag_value="json", help="JSON output")
@click.option("--plain", "-p", "fmt", flag_value="plain", help="TSV output for piping")
@click.option("--markdown", "-md", "fmt", flag_value="markdown", help="Markdown output")
@click.option(
    "--verbose", "-v", is_flag=True, default=False, help="Verbose output (show metrics, timestamps, metadata)"
)
@click.pass_context
def cli(ctx, fmt, verbose):
    """openclaw-x: CLI for X/Twitter API v2."""
    ctx.ensure_object(dict)
    ctx.obj = State(fmt or "human", verbose=verbose)


# ============================================================
# tweet
# ============================================================


@cli.group()
def tweet():
    """Tweet operations."""


@tweet.command("post")
@click.argument("text")
@click.option("--media", "media_path", default=None, type=click.Path(exists=True), help="Path to media file")
@click.option("--poll", default=None, help="Comma-separated poll options")
@click.option("--poll-duration", default=1440, type=int, help="Poll duration in minutes")
@pass_state
def tweet_post(state, text, media_path, poll, poll_duration):
    """Post a tweet."""
    media_ids = None
    if media_path:
        mid = state.upload_media(media_path)
        media_ids = [mid]
    poll_options = [o.strip() for o in poll.split(",")] if poll else None
    data = state.post_and_record(text, media_ids=media_ids, poll_options=poll_options)
    state.output(data, "Posted")


@tweet.command("get")
@click.argument("id_or_url")
@pass_state
def tweet_get(state, id_or_url):
    """Fetch a tweet by ID or URL."""
    tid = parse_tweet_id(id_or_url)
    data = state.client.get_tweet(tid)
    state.output(data, f"Tweet {tid}")


@tweet.command("delete")
@click.argument("id_or_url")
@pass_state
def tweet_delete(state, id_or_url):
    """Delete a tweet."""
    tid = parse_tweet_id(id_or_url)
    data = state.client.delete_tweet(tid)
    state.output(data, "Deleted")


@tweet.command("reply")
@click.argument("id_or_url")
@click.argument("text")
@click.option("--media", "media_path", default=None, type=click.Path(exists=True), help="Path to media file")
@pass_state
def tweet_reply(state, id_or_url, text, media_path):
    """Reply to a tweet.

    NOTE: X restricts programmatic replies. You can only reply if the original
    author @mentioned you or quoted your post. Use 'tweet quote' as a workaround.
    """
    tid = parse_tweet_id(id_or_url)
    click.echo(
        "Warning: X restricts programmatic replies. This will only succeed if "
        "the original author @mentioned you or quoted your post.",
        err=True,
    )
    media_ids = None
    if media_path:
        mid = state.upload_media(media_path)
        media_ids = [mid]
    data = state.post_and_record(text, reply_to=tid, media_ids=media_ids)
    state.output(data, "Reply")


@tweet.command("quote")
@click.argument("id_or_url")
@click.argument("text")
@click.option("--media", "media_path", default=None, type=click.Path(exists=True), help="Path to media file")
@pass_state
def tweet_quote(state, id_or_url, text, media_path):
    """Quote tweet."""
    tid = parse_tweet_id(id_or_url)
    media_ids = None
    if media_path:
        mid = state.upload_media(media_path)
        media_ids = [mid]
    data = state.post_and_record(text, quote_tweet_id=tid, media_ids=media_ids)
    state.output(data, "Quote")


@tweet.command("search")
@click.argument("query")
@click.option("--max", "max_results", default=10, type=int, help="Max results (10-100)")
@pass_state
def tweet_search(state, query, max_results):
    """Search recent tweets."""
    data = state.client.search_tweets(query, max_results)
    state.output(data, f"Search: {query}")


@tweet.command("metrics")
@click.argument("id_or_url")
@pass_state
def tweet_metrics(state, id_or_url):
    """Get tweet engagement metrics."""
    tid = parse_tweet_id(id_or_url)
    data = state.client.get_tweet_metrics(tid)
    state.output(data, f"Metrics {tid}")


# ============================================================
# thread
# ============================================================


@cli.group()
def thread():
    """Thread operations."""


@thread.command("post")
@click.argument("texts", nargs=-1, required=True)
@click.option("--name", default=None, help="Name for the thread (for later continuation)")
@click.option("--file", "file_path", default=None, type=click.Path(exists=True), help="JSON file with tweet texts")
@pass_state
def thread_post(state, texts, name, file_path):
    """Post a thread (multiple tweets chained as replies).

    Provide tweet texts as arguments, or use --file to load from a JSON array.
    """
    tweet_texts: list[str] = []
    if file_path:
        with open(file_path, encoding="utf-8") as f:
            tweet_texts = json.load(f)
        if not isinstance(tweet_texts, list):
            raise click.UsageError("Thread file must contain a JSON array of strings.")
    if texts:
        tweet_texts.extend(texts)
    if not tweet_texts:
        raise click.UsageError("Provide tweet texts as arguments or via --file.")

    previous_tweet_id: str | None = None
    posted: list[dict] = []

    for i, tweet_text in enumerate(tweet_texts):
        data = state.post_and_record(
            tweet_text,
            reply_to=previous_tweet_id,
            thread_name=name,
            parent_id=previous_tweet_id,
        )
        tweet_id = data["data"]["id"]
        previous_tweet_id = tweet_id
        posted.append(data["data"])
        click.echo(f"Tweet {i + 1}/{len(tweet_texts)} posted: https://x.com/i/status/{tweet_id}", err=True)

    result = {"data": posted, "meta": {"thread_name": name, "count": len(posted)}}
    state.output(result, f"Thread: {name or 'unnamed'}")


@thread.command("continue")
@click.argument("name")
@click.argument("text")
@click.option("--media", "media_path", default=None, type=click.Path(exists=True), help="Path to media file")
@pass_state
def thread_continue(state, name, text, media_path):
    """Continue a named thread with a new tweet."""
    latest_id = state.threads.get_thread_latest_id(name)
    media_ids = None
    if media_path:
        mid = state.upload_media(media_path)
        media_ids = [mid]
    data = state.post_and_record(text, reply_to=latest_id, media_ids=media_ids, thread_name=name, parent_id=latest_id)
    state.output(data, f"Thread continued: {name}")


@thread.command("list")
@pass_state
def thread_list(state):
    """List all named threads."""
    threads = state.threads.list_threads()
    if not threads:
        click.echo("No named threads yet. Use --name when posting to track threads.", err=True)
        return
    result = {
        "data": [
            {
                "name": name,
                "latestTweetId": info["latestTweetId"],
                "firstTweetId": info["firstTweetId"],
                "updatedAt": info["updatedAt"],
                "url": f"https://x.com/i/status/{info['firstTweetId']}",
            }
            for name, info in threads.items()
        ]
    }
    state.output(result, "Threads")


@thread.command("history")
@click.argument("name")
@pass_state
def thread_history(state, name):
    """Show tweets in a named thread."""
    tweets = state.threads.get_thread_tweets(name)
    result = {"data": tweets, "meta": {"thread_name": name, "count": len(tweets)}}
    state.output(result, f"Thread: {name}")


# ============================================================
# user
# ============================================================


@cli.group()
def user():
    """User operations."""


@user.command("get")
@click.argument("username")
@pass_state
def user_get(state, username):
    """Look up a user profile."""
    data = state.client.get_user(strip_at(username))
    state.output(data, f"@{strip_at(username)}")


@user.command("timeline")
@click.argument("username")
@click.option("--max", "max_results", default=10, type=int, help="Max results (5-100)")
@pass_state
def user_timeline(state, username, max_results):
    """Fetch a user's recent tweets."""
    uname = strip_at(username)
    user_data = state.client.get_user(uname)
    uid = user_data["data"]["id"]
    data = state.client.get_timeline(uid, max_results)
    state.output(data, f"@{uname} timeline")


@user.command("followers")
@click.argument("username")
@click.option("--max", "max_results", default=100, type=int, help="Max results (1-1000)")
@pass_state
def user_followers(state, username, max_results):
    """List a user's followers."""
    uname = strip_at(username)
    user_data = state.client.get_user(uname)
    uid = user_data["data"]["id"]
    data = state.client.get_followers(uid, max_results)
    state.output(data, f"@{uname} followers")


@user.command("following")
@click.argument("username")
@click.option("--max", "max_results", default=100, type=int, help="Max results (1-1000)")
@pass_state
def user_following(state, username, max_results):
    """List who a user follows."""
    uname = strip_at(username)
    user_data = state.client.get_user(uname)
    uid = user_data["data"]["id"]
    data = state.client.get_following(uid, max_results)
    state.output(data, f"@{uname} following")


# ============================================================
# me
# ============================================================


@cli.group()
def me():
    """Self operations (authenticated user)."""


@me.command("mentions")
@click.option("--max", "max_results", default=10, type=int, help="Max results (5-100)")
@pass_state
def me_mentions(state, max_results):
    """Fetch your recent mentions."""
    data = state.client.get_mentions(max_results)
    state.output(data, "Mentions")


@me.command("bookmarks")
@click.option("--max", "max_results", default=10, type=int, help="Max results (1-100)")
@pass_state
def me_bookmarks(state, max_results):
    """Fetch your bookmarks."""
    data = state.client.get_bookmarks(max_results)
    state.output(data, "Bookmarks")


@me.command("bookmark")
@click.argument("id_or_url")
@pass_state
def me_bookmark(state, id_or_url):
    """Bookmark a tweet."""
    tid = parse_tweet_id(id_or_url)
    data = state.client.bookmark_tweet(tid)
    state.output(data, "Bookmarked")


@me.command("unbookmark")
@click.argument("id_or_url")
@pass_state
def me_unbookmark(state, id_or_url):
    """Remove a bookmark."""
    tid = parse_tweet_id(id_or_url)
    data = state.client.unbookmark_tweet(tid)
    state.output(data, "Unbookmarked")


# ============================================================
# quick actions (top-level)
# ============================================================


@cli.command("like")
@click.argument("id_or_url")
@pass_state
def like(state, id_or_url):
    """Like a tweet."""
    tid = parse_tweet_id(id_or_url)
    data = state.client.like_tweet(tid)
    state.output(data, "Liked")


@cli.command("retweet")
@click.argument("id_or_url")
@pass_state
def retweet(state, id_or_url):
    """Retweet a tweet."""
    tid = parse_tweet_id(id_or_url)
    data = state.client.retweet(tid)
    state.output(data, "Retweeted")


# ============================================================
# history (top-level)
# ============================================================


@cli.command("history")
@click.option("--count", "-n", default=10, type=int, help="Number of recent tweets to show")
@pass_state
def history(state, count):
    """Show recent tweet history."""
    tweets = state.threads.get_recent_tweets(count)
    if not tweets:
        click.echo("No tweet history yet.", err=True)
        return
    result = {"data": tweets, "meta": {"count": len(tweets)}}
    state.output(result, "History")


# ============================================================
# version (top-level)
# ============================================================


@cli.command("version")
def version():
    """Show version."""
    click.echo(f"openclaw-x {__version__}")


def main():
    cli()


if __name__ == "__main__":
    main()
