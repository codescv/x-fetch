import pytest
from typer.testing import CliRunner
from x_fetch.cli import app
from unittest.mock import patch
from pathlib import Path

runner = CliRunner()

@patch("x_fetch.cli.fetch_posts")
def test_cli_basic(mock_fetch_posts):
    mock_fetch_posts.return_value = [{
        "author_name": "Test Author", 
        "author_handle": "@test",
        "posted_at": "Just now",
        "text": "Post 1", 
        "post_link": "", 
        "is_repost": False, 
        "repost_by": "", 
        "comments": "1", 
        "retweets": "2", 
        "likes": "3", 
        "links": [],
        "attachments": [],
        "comments_data": []
    }]
    
    result = runner.invoke(app, ["--query", "test query", "--count", "1"])
    
    assert result.exit_code == 0
    assert "Fetching top 1 posts" in result.stdout
    assert "--- Post 1 ---" in result.stdout
    assert "Author: Test Author" in result.stdout
    
    mock_fetch_posts.assert_called_once()
    kwargs = mock_fetch_posts.call_args.kwargs
    assert kwargs["query"] == "test query"
    assert kwargs["count"] == 1
    assert isinstance(kwargs["user_data_dir"], Path)

@patch("x_fetch.cli.fetch_posts")
def test_cli_missing_source(mock_fetch_posts):
    # No source provided
        result = runner.invoke(app, ["--count", "5"])
        assert result.exit_code != 0
        assert "Error: You must provide exactly one of --query, --handle, --following, or --recommended" in result.output

@patch("x_fetch.cli.open_for_login")
def test_cli_login(mock_open_for_login):
    result = runner.invoke(app, ["login", "--user-data-dir", "/tmp/test-dir"])
    assert result.exit_code == 0
    assert "Opening browser for login" in result.stdout
    mock_open_for_login.assert_called_once()
    kwargs = mock_open_for_login.call_args.kwargs
    assert kwargs["user_data_dir"] == Path("/tmp/test-dir")
