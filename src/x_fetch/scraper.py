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
    screenshot_path: Optional[str] = None,
    with_comments: bool = False
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
            
            # Wait for either tweets or login elements to appear
            try:
                page.wait_for_selector('[data-testid="tweet"], a[data-testid="loginButton"]', timeout=10000)
            except Exception:
                pass
                
            # Check if we are logged out. Usually indicated by URL or login buttons
            is_logged_out = False
            if "i/flow/login" in page.url:
                is_logged_out = True
            elif "explore" in page.url and "explore" not in target_url:
                # Redirected to explore instead of the search/home page
                is_logged_out = True
            else:
                try:
                    # Check for login buttons
                    login_btn = page.query_selector('a[data-testid="loginButton"]')
                    if login_btn:
                        is_logged_out = True
                except Exception:
                    pass

            if is_logged_out:
                print("Error: You are not logged in or cannot view X.com properly.")
                print("Please run the login command first:")
                print(f"x-fetch login --user-data-dir '{user_data_dir}'")
                return []

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
                
            retries = 0
            try:
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
                            
                            // Author breakdown
                            const authorRaw = getText('[data-testid="User-Name"]');
                            const authorParts = authorRaw.split('\\n');
                            const authorName = authorParts.length > 0 ? authorParts[0] : "";
                            const authorHandle = authorParts.length > 1 ? authorParts[1] : "";
                            // Timestamp might be at index 2 if there's no dot, or 3 if there is a dot
                            let postedAt = "";
                            if (authorParts.length > 3) postedAt = authorParts[3];
                            else if (authorParts.length > 2) postedAt = authorParts[2];
                            
                            // Links inside tweet text
                            const textEl = t.querySelector('[data-testid="tweetText"]');
                            const links = textEl ? Array.from(textEl.querySelectorAll('a')).map(a => a.href) : [];
                            
                            // Attachments (Images and Videos)
                            const attachments = [];
                            const photoEls = Array.from(t.querySelectorAll('[data-testid="tweetPhoto"] img'));
                            const videoEls = Array.from(t.querySelectorAll('video'));
                            photoEls.forEach(img => { if(img.src) attachments.push({type: 'image', url: img.src}) });
                            videoEls.forEach(vid => { if(vid.src) attachments.push({type: 'video', url: vid.src}) });

                            // Timestamp / Link to post
                            const timeEl = t.querySelector('a[dir="ltr"] time');
                            const postLink = timeEl && timeEl.parentElement ? timeEl.parentElement.href : "";
                            
                            // Comments, Retweets, Likes
                            const getMetric = (testId) => {
                                const el = t.querySelector(`[data-testid="${testId}"]`);
                                return el ? (el.getAttribute('aria-label') || el.innerText || "") : "";
                            };
                            const comments = getMetric('reply');
                            const retweets = getMetric('retweet');
                            const likes = getMetric('like');
                            
                            // Repost By logic
                            const socialContext = t.querySelector('[data-testid="socialContext"]');
                            let repostBy = "";
                            if (socialContext) {
                                const match = socialContext.innerText.match(/(.+) reposted/i);
                                if (match) repostBy = match[1].trim();
                            }
                            
                            // Identifier for uniqueness
                            const uniqueId = postLink || text + authorName;

                            return {
                                id: uniqueId,
                                author_name: authorName,
                                author_handle: authorHandle,
                                posted_at: postedAt,
                                text: text,
                                links: links,
                                attachments: attachments,
                                post_link: postLink,
                                comments: comments,
                                retweets: retweets,
                                likes: likes,
                                is_repost: !!repostBy,
                                repost_by: repostBy
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
            except KeyboardInterrupt:
                print("\nInterrupted while fetching posts. Returning what we have so far...")
                    
            if len(fetched_posts) > count:
                fetched_posts = fetched_posts[:count]

            # Fetch comments for each post if requested
            if with_comments:
                for post in fetched_posts:
                    if not post.get('post_link'):
                        continue
                    try:
                        page.goto(post['post_link'], wait_until="domcontentloaded")
                        page.wait_for_timeout(2000) # Give comments some time to load
                        
                        replies = page.evaluate('''() => {
                            const tweets = document.querySelectorAll('[data-testid="tweet"]');
                            const results = [];
                            // Start from 1 assuming index 0 is the main post focus
                            for (let i = 1; i < tweets.length; i++) {
                                const t = tweets[i];
                                const getText = (selector) => {
                                    const el = t.querySelector(selector);
                                    return el ? el.innerText : "";
                                };
                                const text = getText('[data-testid="tweetText"]');
                                const authorRaw = getText('[data-testid="User-Name"]');
                                const authorParts = authorRaw.split('\\n');
                                const authorName = authorParts.length > 0 ? authorParts[0] : "";
                                const authorHandle = authorParts.length > 1 ? authorParts[1] : "";
                                const timeEl = t.querySelector('a[dir="ltr"] time');
                                const postLink = timeEl && timeEl.parentElement ? timeEl.parentElement.href : "";
                                
                                results.push({
                                    author_name: authorName,
                                    author_handle: authorHandle,
                                    text: text,
                                    post_link: postLink
                                });
                                if (results.length >= 5) break;
                            }
                            return results;
                        }''')
                        post['comments_data'] = replies
                    except KeyboardInterrupt:
                        print("\nInterrupted while fetching comments. Stopping comment fetch...")
                        break
                    except Exception as e:
                        print(f"Failed to fetch comments for {post.get('post_link')}: {e}")

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
                    print("\nClosing browser...")
            try:
                context.close()
            except Exception:
                pass
            
    return fetched_posts[:count]

def open_for_login(
    user_data_dir: Path,
    http_proxy: Optional[str] = None,
    https_proxy: Optional[str] = None,
    no_proxy: Optional[str] = None,
    executable_path: Optional[str] = None,
) -> None:
    """
    Open X.com in a headed browser to allow the user to log in.
    """
    proxy = get_proxy_settings(http_proxy, https_proxy, no_proxy)

    with sync_playwright() as p:
        browser_info: Dict[str, Any] = {
            "user_data_dir": str(user_data_dir),
            "headless": False,
        }
        if executable_path:
            browser_info["executable_path"] = executable_path
        if proxy:
            browser_info["proxy"] = proxy

        context = p.chromium.launch_persistent_context(**browser_info)
        
        try:
            pages = context.pages
            page = pages[0] if len(pages) > 0 else context.new_page()
            
            print("Opening X.com... Please log in.")
            page.goto("https://x.com/", wait_until="domcontentloaded")
            print("Browser is open in headed mode.")
            print("Close the browser manually or press Ctrl+C in this terminal when you are done.")
            
            page.wait_for_event("close", timeout=0)
        except Exception as e:
            if "Target page, context or browser has been closed" not in str(e) and "Target closed" not in str(e):
                print(f"Browser closed: {e}")
        finally:
            try:
                context.close()
            except Exception:
                pass
