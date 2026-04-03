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

### 1. Authentication

Before fetching from timelines or searching, log into X.com:

```bash
x-fetch login --user-data-dir ~/Documents/x-fetch
```
This opens a headed browser window where you can enter your credentials. Once logged in, close the browser or press `Ctrl+C`. This saves your session for future interactions.

If you skip this step, fetching commands may abort with:
```
Error: You are not logged in or cannot view X.com properly.
Please run the login command first:
x-fetch login --user-data-dir '~/Documents/x-fetch'
```

### 2. Fetching Output

```bash
x-fetch --query "agentic AI" --count 5
x-fetch --handle "tim_cook" --output-format json
x-fetch --following --count 20 --with-comments
x-fetch --recommended --output results.json --output-format json
x-fetch post https://x.com/karpathy/status/2039805659525644595
```

### Options

Fetch Source (You must provide exactly one):
- `--query TEXT`: Search query on X.
- `--handle TEXT`: Fetch posts from a specific user profile.
- `--following`: Fetch from the logged-in user's 'Following' timeline.
- `--recommended`: Fetch from the logged-in user's 'For you' timeline.

Other Options:
- `--count INTEGER`: Number of posts to fetch (default: 10).
- `--with-comments`: Navigate into each post and fetch its top replies.
- `--output-format TEXT`: Output format: `text` or `json` (default: `text`).
- `--output PATH`: Optional path to write output directly to a file (instead of stdout).
- `--user-data-dir PATH`: Path to the Playwright user data directory (default: `~/Documents/x-fetch`). This allows the script to use a logged-in session.
- `--screenshot PATH`: Optional path to save a full-page Chrome screenshot before returning.

## Feature Overview
- **Rich Metadata Extraction**: Extracts pure text alongside authors, embedded links, original post links (for reposts), comments, likes, and retweets.
- **Persistent Sessions**: Leverages Playwright's persistent browser context using your logged-in profile.
- **System Chrome**: Bypasses downloaded Playwright binaries to use native macOS Google Chrome.
- **Proxy Support**: Respects `HTTPS_PROXY` settings for x.com access.

## Agent Skill
Copy `SKILL.md` to your favorite Agents (Claud Code, Gemini CLI, XXXClaw, etc).