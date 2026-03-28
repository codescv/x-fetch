import urllib.request
import urllib.parse
from pathlib import Path
from typing import List, Optional, Dict, Any
from playwright.sync_api import sync_playwright

import os

def get_proxy_settings(
    http_proxy: Optional[str] = None,
    https_proxy: Optional[str] = None,
    no_proxy: Optional[str] = None
) -> Optional[Dict[str, str]]:
    """
    Get system proxy settings to respect system network proxy.
    Extracts http_proxy, https_proxy, and no_proxy from system environment variables,
    with explicit overrides taking priority.
    """
    server = https_proxy or http_proxy
    
    if not server:
        proxies = urllib.request.getproxies()
        server = proxies.get('https') or proxies.get('http')
    
    if not server:
        server = (os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy') or 
                  os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy'))
        
    if server:
        bypass = no_proxy or os.environ.get('NO_PROXY') or os.environ.get('no_proxy')
        proxy_dict = {"server": server}
        if bypass:
            proxy_dict["bypass"] = bypass
        return proxy_dict
        
    return None

def fetch_posts(
    count: int, 
    user_data_dir: Path,
    query: Optional[str] = None,
    handle: Optional[str] = None,
    following: bool = False,
    recommended: bool = False,
    http_proxy: Optional[str] = None,
    https_proxy: Optional[str] = None,
    no_proxy: Optional[str] = None,
    executable_path: Optional[str] = None,
    debug: bool = False,
    wait_on_exit: bool = False,
    screenshot_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Fetch top `count` posts from X using Playwright caching.
    
    Args:
        count: Minimum number of posts to fetch.
        user_data_dir: Playwright persistent data directory path.
        query: Search term for X.
        handle: Fetch from a specific user profile.
        following: Fetch from the 'Following' timeline.
        recommended: Fetch from the 'For you' timeline.
    
    Returns:
        A list of dictionaries containing post text and metadata.
    """
    proxy = get_proxy_settings(http_proxy, https_proxy, no_proxy)
    
    if query:
        encoded_query = urllib.parse.quote(query)
        target_url = f"https://x.com/search?q={encoded_query}&src=typed_query"
    elif handle:
        target_url = f"https://x.com/{handle.lstrip('@')}"
    elif following:
        target_url = "https://x.com/home"
    elif recommended:
        target_url = "https://x.com/home"
    else:
        raise ValueError("Must provide one of query, handle, following, or recommended")
        
    fetched_posts: List[Dict[str, Any]] = []
    seen_posts = set()
    
    with sync_playwright() as p:
        browser_info: Dict[str, Any] = {
            "user_data_dir": str(user_data_dir),
            "headless": not debug,
        }
        if executable_path:
            browser_info["executable_path"] = executable_path
        if proxy:
            browser_info["proxy"] = proxy
            
        context = p.chromium.launch_persistent_context(**browser_info)
        
        try:
            # Instead of opening a new page right away, we can use an existing one or create a new one.
            pages = context.pages
            page = pages[0] if len(pages) > 0 else context.new_page()
            
            page.goto(target_url, wait_until="domcontentloaded")
            
            # Handle timeline tabs if needed
            if following or recommended:
                try:
                    tab_name = "Following" if following else "For you"
                    # X uses role="tab"
                    tab_selector = f'div[role="tab"] span:has-text("{tab_name}")'
                    page.wait_for_selector(tab_selector, timeout=10000)
                    page.locator(tab_selector).first.click()
                    page.wait_for_timeout(2000) # Wait for timeline to switch
                except Exception as e:
                    print(f"Failed to switch to {tab_name} tab: {e}")

            # Wait for the first tweet or at least a few seconds for X to load results
            try:
                page.wait_for_selector('[data-testid="tweet"]', timeout=20000)
            except Exception as e:
                # If X prompts for login, or there's some overlay blocking, we will still try to parse
                pass
                
            retries = 0
            while len(fetched_posts) < count and retries < 10:
                new_posts = page.evaluate('''() => {
                    const tweets = document.querySelectorAll('[data-testid="tweet"]');
                    return Array.from(tweets).map(t => {
                        // Safe extraction helper
                        const getText = (selector) => {
                            const el = t.querySelector(selector);
                            return el ? el.innerText : "";
                        };

                        const text = getText('[data-testid="tweetText"]');
                        
                        // Author
                        const author = getText('[data-testid="User-Name"]');
                        
                        // Links inside tweet text
                        const textEl = t.querySelector('[data-testid="tweetText"]');
                        const links = textEl ? Array.from(textEl.querySelectorAll('a')).map(a => a.href) : [];
                        
                        // Timestamp / Link to post
                        const timeEl = t.querySelector('a[dir="ltr"] time');
                        const postLink = timeEl && timeEl.parentElement ? timeEl.parentElement.href : "";
                        
                        // Comments, Retweets, Likes (using aria-label or inner text)
                        // It's often easier to get the aria-label of the 'reply', 'retweet', 'like' testids
                        const getMetric = (testId) => {
                            const el = t.querySelector(`[data-testid="${testId}"]`);
                            return el ? (el.getAttribute('aria-label') || el.innerText || "") : "";
                        };
                        const comments = getMetric('reply');
                        const retweets = getMetric('retweet');
                        const likes = getMetric('like');
                        
                        // Original post link for reposts
                        const socialContext = t.querySelector('[data-testid="socialContext"]');
                        const isRepost = socialContext && socialContext.innerText.toLowerCase().includes('reposted');
                        
                        // Identifier for uniqueness
                        const uniqueId = postLink || text + author;

                        return {
                            id: uniqueId,
                            author: author,
                            text: text,
                            links: links,
                            post_link: postLink,
                            comments: comments,
                            retweets: retweets,
                            likes: likes,
                            is_repost: !!isRepost,
                            social_context: socialContext ? socialContext.innerText : ""
                        };
                    });
                }''')
                
                added_any = False
                for post_data in new_posts:
                    post_id = post_data.get('id', '')
                    if not post_id:
                        continue
                    if post_id not in seen_posts:
                        seen_posts.add(post_id)
                        fetched_posts.append(post_data)
                        added_any = True
                        if len(fetched_posts) >= count:
                            break
                            
                if len(fetched_posts) >= count:
                    break
                    
                # Scroll down
                page.evaluate('window.scrollBy(0, document.body.scrollHeight);')
                page.wait_for_timeout(2000) # Give it 2 seconds to load new tweets
                
                if not added_any:
                    retries += 1
                else:
                    retries = 0
                    
        finally:
            if screenshot_path:
                try:
                    page.screenshot(path=screenshot_path, full_page=True)
                    print(f"Screenshot saved to {screenshot_path}")
                except Exception as e:
                    print(f"Failed to save screenshot: {e}")

            if wait_on_exit:
                import time
                print("\nWaiting on exit... Press Ctrl+C to close the browser.")
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    pass
            context.close()
            
    return fetched_posts[:count]
