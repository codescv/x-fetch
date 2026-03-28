import typer
from pathlib import Path
import json
from .scraper import fetch_posts

app = typer.Typer(help="X (Twitter) automator tool based on python playwright.")

@app.command()
def main(
    query: str = typer.Option(None, "--query", help="Search query on X"),
    handle: str = typer.Option(None, "--handle", help="Fetch posts from a specific user profile"),
    following: bool = typer.Option(False, "--following", help="Fetch from the 'Following' timeline"),
    recommended: bool = typer.Option(False, "--recommended", help="Fetch from the 'For you' timeline"),
    output: str = typer.Option("text", "--output", help="Output format (text, json)"),
    screenshot: str = typer.Option(None, "--screenshot", help="Path to save a screenshot before returning"),
    count: int = typer.Option(10, "--count", help="Number of posts to fetch"),
    user_data_dir: Path = typer.Option(
        Path.home() / "Documents" / "x-fetch",
        "--user-data-dir",
        dir_okay=True,
        help="Path to the Playwright user data directory"
    ),
    http_proxy: str = typer.Option(None, "--http-proxy", help="HTTP proxy server"),
    https_proxy: str = typer.Option(None, "--https-proxy", help="HTTPS proxy server"),
    no_proxy: str = typer.Option(None, "--no-proxy", help="Comma-separated bypass domains"),
    executable_path: str = typer.Option(
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "--executable-path",
        help="Path to the browser executable"
    ),
    debug: bool = typer.Option(False, "--debug", help="If true, run browser in headed mode (headless=False)"),
    wait_on_exit: bool = typer.Option(False, "--wait-on-exit", help="If true, keep browser open until Ctrl+C")
):
    """
    Fetch top K posts from X (Twitter).
    """
    sources = [s for s in [query, handle, following, recommended] if s]
    if len(sources) != 1:
        typer.secho("Error: You must provide exactly one of --query, --handle, --following, or --recommended", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    if output not in ["text", "json"]:
        typer.secho("Error: Output format must be 'text' or 'json'", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    if output == "text":
        typer.echo(f"Fetching top {count} posts...")
        typer.echo(f"Using user data directory: {user_data_dir}")
    
    try:
        posts = fetch_posts(
            count=count, 
            user_data_dir=user_data_dir,
            query=query,
            handle=handle,
            following=following,
            recommended=recommended,
            http_proxy=http_proxy,
            https_proxy=https_proxy,
            no_proxy=no_proxy,
            executable_path=executable_path,
            debug=debug,
            wait_on_exit=wait_on_exit,
            screenshot_path=screenshot
        )
        
        if output == "json":
            typer.echo(json.dumps(posts, indent=2, ensure_ascii=False))
        else:
            typer.echo(f"\nSuccessfully fetched {len(posts)} posts.\n")
            
            for i, post in enumerate(posts, start=1):
                typer.echo(f"--- Post {i} ---")
                typer.echo(f"Author: {post.get('author')}")
                if post.get('is_repost'):
                    typer.echo(f"Reposted. Context: {post.get('social_context')}")
                typer.echo(f"Text:\n{post.get('text')}")
                if post.get('post_link'):
                    typer.echo(f"Link: {post.get('post_link')}")
                typer.echo(f"Comments: {post.get('comments')} | Retweets: {post.get('retweets')} | Likes: {post.get('likes')}")
                if post.get('links'):
                    typer.echo(f"Contained Links: {', '.join(post.get('links'))}")
                typer.echo("-" * 40)
            
    except Exception as e:
        typer.secho(f"Error fetching posts: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()
