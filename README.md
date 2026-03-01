# openclaw-x

Full-featured CLI and [OpenClaw](https://github.com/AmuMoon/openclaw) skill for X/Twitter API v2.

## Features

- **Tweet operations**: post, get, delete, reply, quote, search, metrics
- **Media upload**: JPG, PNG, WEBP, GIF, MP4 via chunked upload (no tweepy)
- **Threads**: create, continue, name, and track threaded conversations
- **User operations**: lookup, timeline, followers, following
- **Engagement**: like, retweet, bookmark
- **Self operations**: mentions, bookmarks
- **History**: local tracking of all posted tweets and threads
- **Multiple output formats**: JSON, human-readable (rich), TSV, Markdown
- **OpenClaw integration**: ready-to-use skill definition and agent templates

## Installation

```bash
# With uv (recommended)
uv tool install openclaw-x

# With pip
pip install openclaw-x
```

## Configuration

Set your X API credentials. Get them at [developer.x.com](https://developer.x.com/en/portal/dashboard).

```bash
mkdir -p ~/.config/openclaw-x
cat > ~/.config/openclaw-x/.env << 'EOF'
X_API_KEY=your_api_key
X_API_SECRET=your_api_secret
X_ACCESS_TOKEN=your_access_token
X_ACCESS_TOKEN_SECRET=your_access_token_secret
X_BEARER_TOKEN=your_bearer_token
EOF
```

Or set environment variables directly / use a `.env` file in your working directory.

## Usage

```bash
# Post a tweet
openclaw-x tweet post "Hello from openclaw-x!"

# Post with media
openclaw-x tweet post "Check this out" --media /path/to/image.jpg

# Search tweets (JSON output)
openclaw-x -j tweet search "AI agents" --max 20

# Post a thread
openclaw-x thread post "First tweet" "Second tweet" "Third tweet" --name my-thread

# Continue the thread later
openclaw-x thread continue my-thread "Another tweet in the thread"

# Get a user profile
openclaw-x user get @username

# Like a tweet
openclaw-x like https://x.com/user/status/1234567890

# View your mentions
openclaw-x me mentions

# See tweet history
openclaw-x history
```

## CLI Reference

```
openclaw-x [-j|--json] [-p|--plain] [-md|--markdown] [-v|--verbose]
├── tweet post TEXT [--media PATH] [--poll OPTIONS]
├── tweet get ID_OR_URL
├── tweet delete ID_OR_URL
├── tweet reply ID_OR_URL TEXT [--media PATH]
├── tweet quote ID_OR_URL TEXT [--media PATH]
├── tweet search QUERY [--max N]
├── tweet metrics ID_OR_URL
├── thread post TEXT... [--name NAME] [--file PATH]
├── thread continue NAME TEXT [--media PATH]
├── thread list
├── thread history NAME
├── user get USERNAME
├── user timeline USERNAME [--max N]
├── user followers USERNAME [--max N]
├── user following USERNAME [--max N]
├── me mentions [--max N]
├── me bookmarks [--max N]
├── me bookmark ID_OR_URL
├── me unbookmark ID_OR_URL
├── like ID_OR_URL
├── retweet ID_OR_URL
├── history [--count N]
└── version
```

## Output Formats

| Flag | Format | Use Case |
|------|--------|----------|
| (default) | Rich panels/tables | Interactive terminal use |
| `-j` | JSON | Agent consumption, scripting |
| `-p` | TSV | Piping to other tools |
| `-md` | Markdown | Documentation, reports |

## OpenClaw Integration

Install as an OpenClaw skill:

```bash
# The skill definition is in skill/SKILL.md
openclaw skills add openclaw-x /path/to/openclaw-x-skill/skill
```

## Development

```bash
git clone https://github.com/AmuMoon/openclaw-x-skill.git
cd openclaw-x-skill
uv sync --group dev
uv run pytest tests/ -v
uv run ruff check src/ tests/
```

## License

MIT
