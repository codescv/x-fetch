import typer
from pathlib import Path
from .scraper import fetch_posts

app = typer.Typer(help="X (Twitter) automator tool based on python playwright.")

@app.command()
def main(
    query: str = typer.Option(..., "--query", help="Search query on X"),
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
    Fetch top K posts from X (Twitter) based on a search query.
    """
    typer.echo(f"Fetching top {count} posts for query: '{query}'")
    typer.echo(f"Using user data directory: {user_data_dir}")
    
    try:
        posts = fetch_posts(
            query=query, 
            count=count, 
            user_data_dir=user_data_dir,
            http_proxy=http_proxy,
            https_proxy=https_proxy,
            no_proxy=no_proxy,
            executable_path=executable_path,
            debug=debug,
            wait_on_exit=wait_on_exit
        )
        typer.echo(f"\nSuccessfully fetched {len(posts)} posts.\n")
        
        for i, post in enumerate(posts, start=1):
            typer.echo(f"--- Post {i} ---")
            typer.echo(post)
            typer.echo("-" * 40)
            
    except Exception as e:
        typer.secho(f"Error fetching posts: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()
