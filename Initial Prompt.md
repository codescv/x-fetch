# Minimal Viable Product
Build a x(twitter) automator tool based on python playwright.

The initial features:
- Supports fetching top k (`--count`) posts with a search query (`--query`).
- Supports passing a user directory (`--user-data-dir`, default value `~/Documents/x-fetch`) for the playwright browser.
- Respect system network proxy settings

I have a logged in user directory at `~/Documents/x-fetch`. Please test your code with it and make sure it can fetch posts.