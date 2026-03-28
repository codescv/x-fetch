import typer
from pathlib import Path
import json
from .scraper import fetch_posts, open_for_login

app = typer.Typer(help="X (Twitter) automator tool based on python playwright.")

@app.command()
def login(
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
    )
):
    """
    Open X.com in a headed browser to allow manual login.
    """
    typer.echo("Opening browser for login. Please complete login, then close browser or press Ctrl+C.")
    try:
        open_for_login(
            user_data_dir=user_data_dir,
            http_proxy=http_proxy,
            https_proxy=https_proxy,
            no_proxy=no_proxy,
            executable_path=executable_path
        )
    except KeyboardInterrupt:
        typer.echo("\\nLogin process interrupted.")
    except Exception as e:
        typer.secho(f"Error during login: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    query: str = typer.Option(None, "--query", help="Search query on X"),
    handle: str = typer.Option(None, "--handle", help="Fetch posts from a specific user profile"),
    following: bool = typer.Option(False, "--following", help="Fetch from the 'Following' timeline"),
    recommended: bool = typer.Option(False, "--recommended", help="Fetch from the 'For you' timeline"),
    output_format: str = typer.Option("text", "--output-format", help="Output format (text, json)"),
    output: Path = typer.Option(None, "--output", help="Path to write output to file"),
    screenshot: str = typer.Option(None, "--screenshot", help="Path to save a screenshot before returning"),
    with_comments: bool = typer.Option(False, "--with-comments", help="Fetch top replies for each post"),
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
    if ctx.invoked_subcommand is not None:
        return

    sources = [s for s in [query, handle, following, recommended] if s]
    if len(sources) != 1:
        typer.secho("Error: You must provide exactly one of --query, --handle, --following, or --recommended", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    if output_format not in ["text", "json"]:
        typer.secho("Error: Output format must be 'text' or 'json'", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    if output_format == "text":
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
            screenshot_path=screenshot,
            with_comments=with_comments
        )
        
        result_text = ""
        if output_format == "json":
            result_text = json.dumps(posts, indent=2, ensure_ascii=False)
        else:
            lines = [f"\\nSuccessfully fetched {len(posts)} posts.\\n"]
            for i, post in enumerate(posts, start=1):
                lines.append(f"--- Post {i} ---")
                lines.append(f"Author: {post.get('author_name')} ({post.get('author_handle')}) · {post.get('posted_at')}")
                if post.get('is_repost'):
                    lines.append(f"Reposted. Context: {post.get('repost_by')}")
                lines.append(f"Text:\\n{post.get('text')}")
                if post.get('post_link'):
                    lines.append(f"Link: {post.get('post_link')}")
                lines.append(f"Comments: {post.get('comments')} | Retweets: {post.get('retweets')} | Likes: {post.get('likes')}")
                
                attachments = post.get('attachments', [])
                if attachments:
                    lines.append(f"Attachments: {len(attachments)} item(s)")
                if post.get('links'):
                    lines.append(f"Contained Links: {', '.join(post.get('links'))}")
                    
                comments_data = post.get('comments_data', [])
                if comments_data:
                    lines.append("\\n  [Replies]")
                    for j, c in enumerate(comments_data, start=1):
                        lines.append(f"  {j}. {c.get('author_name')} ({c.get('author_handle')}): {c.get('text')}")
                        
                lines.append("-" * 40)
            result_text = "\\n".join(lines)
            
        if output:
            try:
                with open(output, "w", encoding="utf-8") as f:
                    f.write(result_text)
                typer.echo(f"Output successfully written to {output}")
            except Exception as e:
                typer.secho(f"Error writing to file: {e}", fg=typer.colors.RED, err=True)
                raise typer.Exit(code=1)
                
        if debug or not output:
            typer.echo(result_text)
            
    except Exception as e:
        typer.secho(f"Error fetching posts: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()
