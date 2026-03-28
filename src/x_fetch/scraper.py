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
    query: str, 
    count: int, 
    user_data_dir: Path,
    http_proxy: Optional[str] = None,
    https_proxy: Optional[str] = None,
    no_proxy: Optional[str] = None,
    executable_path: Optional[str] = None,
    debug: bool = False,
    wait_on_exit: bool = False
) -> List[str]:
    """
    Fetch top `count` posts for the given `query` using Playwright caching.
    
    Args:
        query: Search term for X.
        count: Minimum number of posts to fetch.
        user_data_dir: Playwright persistent data directory path.
        http_proxy: Explicit HTTP proxy URL.
        https_proxy: Explicit HTTPS proxy URL.
        no_proxy: Explicit domains to bypass proxy.
    
    Returns:
        A list of post text contents.
    """
    proxy = get_proxy_settings(http_proxy, https_proxy, no_proxy)
    encoded_query = urllib.parse.quote(query)
    search_url = f"https://x.com/search?q={encoded_query}&src=typed_query"
    
    fetched_posts: List[str] = []
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
            
            page.goto(search_url, wait_until="domcontentloaded")
            
            # Wait for the first tweet or at least a few seconds for X to load results
            try:
                page.wait_for_selector('[data-testid="tweetText"]', timeout=20000)
            except Exception as e:
                # If X prompts for login, or there's some overlay blocking, we will still try to parse
                pass
                
            retries = 0
            while len(fetched_posts) < count and retries < 10:
                new_posts = page.evaluate('''() => {
                    const tweets = document.querySelectorAll('[data-testid="tweetText"]');
                    return Array.from(tweets).map(t => t.innerText);
                }''')
                
                added_any = False
                for post_text in new_posts:
                    if post_text not in seen_posts:
                        seen_posts.add(post_text)
                        fetched_posts.append(post_text)
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
