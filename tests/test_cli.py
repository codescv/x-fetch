import pytest
from typer.testing import CliRunner
from x_fetch.cli import app
from unittest.mock import patch
from pathlib import Path

runner = CliRunner()

@patch("x_fetch.cli.fetch_posts")
def test_cli_basic(mock_fetch_posts):
    mock_fetch_posts.return_value = ["Post 1", "Post 2"]
    
    result = runner.invoke(app, ["--query", "test query", "--count", "2"])
    
    assert result.exit_code == 0
    assert "Fetching top 2 posts for query: 'test query'" in result.stdout
    assert "--- Post 1 ---" in result.stdout
    assert "--- Post 2 ---" in result.stdout
    
    mock_fetch_posts.assert_called_once()
    kwargs = mock_fetch_posts.call_args.kwargs
    assert kwargs["query"] == "test query"
    assert kwargs["count"] == 2
    assert isinstance(kwargs["user_data_dir"], Path)

@patch("x_fetch.cli.fetch_posts")
def test_cli_missing_query(mock_fetch_posts):
    # Query is required
    result = runner.invoke(app, ["--count", "5"])
    assert result.exit_code != 0
    assert "Missing option '--query'" in result.output
