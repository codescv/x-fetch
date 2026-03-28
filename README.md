# x-fetch

A Python CLI tool for automating fetches posts from X (Twitter).

## Prerequisites
- **uv**: Modern Python project manager.

## Installation

You can install this tool globally using `uv` directly from the repository:

```bash
uv tool install git+https://github.com/your-repo/x-fetch.git
```

Alternatively, to run it from source:

```bash
uv run x-fetch --help
```

## Usage

```bash
x-fetch --query "agentic AI" --count 5
x-fetch --handle "tim_cook" --output json
x-fetch --following --count 20
x-fetch --recommended
```

### Options

Fetch Source (You must provide exactly one):
- `--query TEXT`: Search query on X.
- `--handle TEXT`: Fetch posts from a specific user profile.
- `--following`: Fetch from the logged-in user's 'Following' timeline.
- `--recommended`: Fetch from the logged-in user's 'For you' timeline.

Other Options:
- `--count INTEGER`: Number of posts to fetch (default: 10).
- `--output TEXT`: Output format: `text` or `json` (default: `text`).
- `--user-data-dir PATH`: Path to the Playwright user data directory (default: `~/Documents/x-fetch`). This allows the script to use a logged-in session.
- `--screenshot PATH`: Optional path to save a full-page Chrome screenshot before returning.

## Feature Overview
- **Rich Metadata Extraction**: Extracts pure text alongside authors, embedded links, original post links (for reposts), comments, likes, and retweets.
- **Persistent Sessions**: Leverages Playwright's persistent browser context using your logged-in profile.
- **System Chrome**: Bypasses downloaded Playwright binaries to use native macOS Google Chrome.
- **Proxy Support**: Respects `HTTPS_PROXY` settings for x.com access.
