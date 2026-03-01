---
name: openclaw-x
description: Full-featured X/Twitter CLI — post tweets, threads, media, search, engage, and track history. Use when the user wants to interact with X/Twitter.
---

# OpenClaw X Skill

Interact with X (formerly Twitter) via the `openclaw-x` CLI. Supports posting, searching, engagement, media uploads, threaded conversations, and history tracking.

## Setup Check

Ensure the CLI is installed and credentials are configured:
```bash
# Install (if not already)
uv tool install openclaw-x
# Or: pip install openclaw-x

# Verify
openclaw-x version
```

If credentials are not configured, guide the user:
```bash
mkdir -p ~/.config/openclaw-x
cp /path/to/openclaw-x-skill/.env.example ~/.config/openclaw-x/.env
# User must edit ~/.config/openclaw-x/.env with their X API credentials
```

Required env vars: `X_API_KEY`, `X_API_SECRET`, `X_ACCESS_TOKEN`, `X_ACCESS_TOKEN_SECRET`, `X_BEARER_TOKEN`.

## Commands

Always use `--json` (`-j`) flag when calling from an agent so output is machine-readable.

### Post a tweet
```bash
openclaw-x -j tweet post "Your tweet text here"
```

### Post with media
```bash
openclaw-x -j tweet post "Tweet with image" --media /absolute/path/to/image.jpg
```

### Reply to a tweet
```bash
openclaw-x -j tweet reply <tweet_id_or_url> "Your reply text"
openclaw-x -j tweet reply <tweet_id_or_url> "Reply with image" --media /path/to/image.jpg
```

### Quote tweet
```bash
openclaw-x -j tweet quote <tweet_id_or_url> "Your quote text"
```

### Get a tweet
```bash
openclaw-x -j tweet get <tweet_id_or_url>
```

### Delete a tweet
```bash
openclaw-x -j tweet delete <tweet_id_or_url>
```

### Search tweets
```bash
openclaw-x -j tweet search "search query" --max 20
```

### Tweet metrics
```bash
openclaw-x -j tweet metrics <tweet_id_or_url>
```

### Post a thread
```bash
openclaw-x -j thread post "First tweet" "Second tweet" "Third tweet" --name "thread-name"
openclaw-x -j thread post --file /path/to/thread.json --name "my-thread"
```

Thread JSON format: `["First tweet", "Second tweet", "Third tweet"]`

### Continue a thread
```bash
openclaw-x -j thread continue "thread-name" "Next tweet in thread"
openclaw-x -j thread continue "thread-name" "With media" --media /path/to/image.jpg
```

### List threads
```bash
openclaw-x -j thread list
```

### Thread history
```bash
openclaw-x -j thread history "thread-name"
```

### User lookup
```bash
openclaw-x -j user get username
openclaw-x -j user timeline username --max 20
openclaw-x -j user followers username --max 100
openclaw-x -j user following username --max 100
```

### Self operations
```bash
openclaw-x -j me mentions --max 20
openclaw-x -j me bookmarks --max 20
openclaw-x -j me bookmark <tweet_id_or_url>
openclaw-x -j me unbookmark <tweet_id_or_url>
```

### Engagement
```bash
openclaw-x -j like <tweet_id_or_url>
openclaw-x -j retweet <tweet_id_or_url>
```

### History
```bash
openclaw-x -j history --count 20
```

## Guidelines

- **Character limit**: 280 chars (Premium users may have extended limits)
- **Media**: JPG, PNG, WEBP, GIF, MP4 supported. Use absolute paths.
- **Thread naming**: Use `--name` to track threads for later continuation
- **Tweet IDs**: From `https://x.com/user/status/1234567890` the ID is `1234567890`. Both full URLs and raw IDs are accepted.
- **Rate limits**: X API has rate limits. If you get a rate limit error, wait and retry.
- **Reply restrictions**: X restricts programmatic replies. Replies only succeed if the original author @mentioned you or quoted your post. Use quote tweets as a workaround.

## When User Asks to Post

1. Help craft content within character limits
2. Run the appropriate command with `-j` flag
3. Parse the JSON response and share the resulting tweet URL
4. If starting a thread they may want to continue later, use `--name` to track it
5. For media posts, ensure the file path is absolute

## Output Modes

- `-j` / `--json`: JSON (recommended for agents)
- `-p` / `--plain`: TSV for piping
- `-md` / `--markdown`: Markdown formatted
- Default: Rich human-readable output
