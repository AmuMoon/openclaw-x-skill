# Changelog

## [0.1.0] - 2026-03-01

### Added
- Initial release
- OAuth 1.0a authentication with hand-written HMAC-SHA1 signing
- Full tweet operations: post, get, delete, reply, quote, search, metrics
- Media upload via chunked upload (INIT/APPEND/FINALIZE/STATUS) — no tweepy dependency
- Thread support: create, continue, name, list, and view history
- User operations: lookup, timeline, followers, following
- Engagement: like, retweet
- Bookmark management: list, add, remove
- Mentions monitoring
- Local tweet/thread history tracking (~/.config/openclaw-x/thread-history.json)
- Four output formats: JSON, human (rich), TSV, Markdown
- OpenClaw skill definition (skill/SKILL.md)
- Agent identity and behavioral guidelines (agent/)
- CI workflow (lint + test across Python 3.11-3.13)
- Release workflow (tag-based PyPI publish)
