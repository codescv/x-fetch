import os
import pytest
from x_fetch.scraper import get_proxy_settings
from unittest.mock import patch

@patch.dict(os.environ, {"HTTPS_PROXY": "http://proxy:8080", "NO_PROXY": "localhost,127.0.0.1"}, clear=True)
@patch("urllib.request.getproxies", return_value={})
def test_get_proxy_settings_env(mock_getproxies):
    proxy = get_proxy_settings()
    assert proxy == {"server": "http://proxy:8080", "bypass": "localhost,127.0.0.1"}

@patch.dict(os.environ, {}, clear=True)
@patch("urllib.request.getproxies")
def test_get_proxy_settings_urllib(mock_getproxies):
    mock_getproxies.return_value = {"http": "http://127.0.0.1:80"}
    proxy = get_proxy_settings()
    assert proxy == {"server": "http://127.0.0.1:80"}

@patch.dict(os.environ, {}, clear=True)
@patch("urllib.request.getproxies", return_value={})
def test_get_proxy_settings_empty(mock_getproxies):
    proxy = get_proxy_settings()
    assert proxy is None
