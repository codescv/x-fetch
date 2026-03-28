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
```

### Options

- `--query TEXT`: Search query on X (required).
- `--count INTEGER`: Number of posts to fetch (default: 10).
- `--user-data-dir PATH`: Path to the Playwright user data directory (default: `~/Documents/x-fetch`). This allows the script to use a logged-in session.

## Feature Overview
- **Persistent Sessions**: Leverages Playwright's persistent browser context using your logged-in profile.
- **System Chrome**: Bypasses downloaded Playwright binaries to use native macOS Google Chrome.
- **Proxy Support**: Respects `HTTPS_PROXY` settings for x.com access.
