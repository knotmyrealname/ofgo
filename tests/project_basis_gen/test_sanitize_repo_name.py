import pytest
from project_agent_gen import sanitize_repo_name

def test_sanitize_repo_name_basic():
    assert sanitize_repo_name("https://github.com/foo/bar.git") == "bar"

def test_sanitize_repo_name_no_git():
    assert sanitize_repo_name("https://github.com/foo/bar") == "bar"

def test_sanitize_repo_name_invalid():
    with pytest.raises(ValueError):
        sanitize_repo_name("https://github.com/foo/")

