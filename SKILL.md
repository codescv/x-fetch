---
name: x-fetch
description: Automate fetching posts, profiles, and timelines from X (Twitter) using the x-fetch CLI tool. Use this skill when you need to extract data from x.com for analysis, monitoring, or content aggregation.
---

# x-fetch Skill

This skill provides instructions for installing and using `x-fetch`, a Python CLI tool for scraping X (Twitter) content.

## Prerequisites

Check if `x-fetch` command is executable, if not, install using this command:
```bash
which x-fetch || uv tool install --default-index https://pypi.org/simple git+https://github.com/codescv/x-fetch.git
```

## Prerequisites

- **Google Chrome**: The tool uses the native macOS Google Chrome. Ensure it is installed in `/Applications/Google Chrome.app`.
- **Logged-in Session**: The tool leverages persistent browser contexts. You should ideally have a logged-in session in the default user data directory (`~/Documents/x-fetch`) to access "Following" or "Recommended" timelines.

## Usage Patterns

### 1. Search by Query
Fetch posts matching a specific keyword or phrase.
```bash
x-fetch --query "agentic AI" --count 10 --with-comments
```

### 2. Fetch User Profile
Extract posts from a specific X handle.
```bash
x-fetch --handle "tim_cook" --count 5
```

### 3. Fetch Timelines
Fetch from the logged-in user's timelines.
- **Following**: `x-fetch --following --count 20`
- **Recommended (For You)**: `x-fetch --recommended --count 20`

### 4. Fetch Single Post and Comments
Fetch a specific post and its comments using the post URL.
```bash
x-fetch post "https://x.com/username/status/123456789"
```

### 5. Advanced Options
- **With Comments**: Include top replies for each post.
  `x-fetch --query "GPT-5" --with-comments`
- **Output Format**: Save results as JSON for programmatic processing.
  `x-fetch --query "OpenAI" --count 5 --output-format json --output results.json`
- **Screenshots**: Save a full-page screenshot of the results.
  `x-fetch --query "SpaceX" --screenshot snapshot.png`

## Best Practices for Agents

- **Check Installation**: Before running, verify if `x-fetch` is in the path. If not, perform the installation.
- **Understand user asks**: When user asks for `twitter updates`, they are asking for their followed / timeline updates, NOT their OWN updates.
- **Handle Proxies**: The tool respects `HTTPS_PROXY` environment variables. Ensure they are set if x.com is restricted.
- **Data Directory**: If you need to use a specific logged-in profile, use the `--user-data-dir` flag.
- **JSON Parsing**: When using `--output-format json`, you can read the resulting file and process the metadata (author, text, links, likes, retweets) directly.
- **Error Handling**: It can raise errors when there are network / log in issues. Pass error messages responsibly back to the user.
- **Fetch Comments too**: Comments can also have useful information, so it's recommended to fetch comments when possible.