# Design Document: x-fetch MVP

## Architecture & Responsibilities

The tool is split into two primary layers:
1. **CLI Layer (`cli.py`)**: Uses `typer` to handle user input parsing, default values, and outputs results. It isolates Typer dependencies.
2. **Scraper Layer (`scraper.py`)**: Centralizes interactions with Playwright.

## Playwright Approach

- **Persistent Context**: Uses `launch_persistent_context` to retain cookies, local storage, and active sessions so the user won’t have to log into X (Twitter) for each scrape.
- **System Browser**: Uses the local `/Applications/Google Chrome.app/...` executable to avoid Playwright binary restrictions or missing downloads.
- **Proxy Settings**: The `get_proxy_settings()` function explicitly forces routing through proxy.
- **Source Routing**: Handles navigation directly via JS or URLs depending on target. (e.g., `/search` for queries, `/{handle}` for users, `/home` then tab-clicking for timelines).
- **Deep DOM Evaluation vs Waiting**: X UI elements load dynamically. Instead of relying purely on Playwright selectors from python, we inject a robust JavaScript evaluation snippet that deeply queries properties within each `[data-testid="tweet"]` container. Finding inner elements (Author, Text, Links, and interactions like Retweets/Likes/Replies via `aria-label`) safely ensures scraping doesn't throw fatal node disconnected exceptions.

## Testing Strategy
- The CLI component is unit tested via Playwright mocks, verifying that parameters are correctly parsed and passed.
- The default test directory structure ensures `uv run pytest` seamlessly executes CLI unit tests (`test_cli.py`) and Scraper unit tests (`test_scraper.py`).
