import os
import sys
import re
import pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from unittest.mock import MagicMock

sys.modules['harness_gen'] = MagicMock()
sys.modules['oss_fuzz_gen_onboarding'] = MagicMock()
sys.modules['logger_config'] = MagicMock()
sys.modules['openai'] = MagicMock()
sys.modules['email_validator'] = MagicMock(
    validate_email=lambda email: type('ValidatedEmail', (), {'email': email})()
)

import ofgo


def test_check_email_valid():
    assert ofgo.check_email('test@example.com') == 'test@example.com'

def test_check_email_invalid_regex():
    with pytest.raises(ValueError) as exc:
        ofgo.check_email('bad-email')
    assert 'Invalid email' in str(exc.value)

def test_check_email_invalid_domain():
    with pytest.raises(ValueError):
        ofgo.check_email('x@y')


def test_sanitize_repo_valid():
    url = 'https://github.com/test/project'
    out = ofgo.sanitize_repo(url)
    assert out == 'https://github.com/test/project'

def test_sanitize_repo_invalid_format():
    with pytest.raises(ValueError) as exc:
        ofgo.sanitize_repo('notaurl')
    assert 'Cannot access repository' in str(exc.value)

def test_sanitize_repo_wrong_domain():
    with pytest.raises(ValueError) as exc:
        ofgo.sanitize_repo('https://example.com/repo')
    assert 'not GitHub or GitLab' in str(exc.value)

def test_sanitize_repo_not_https():
    with pytest.raises(ValueError) as exc:
        ofgo.sanitize_repo('http://github.com/test')
    assert 'not HTTPS' in str(exc.value)


def test_project_exists_false(monkeypatch):
    monkeypatch.setattr(ofgo, 'BASE_DIR', '/tmp/nonexistent')
    assert not ofgo.project_exists('proj')

def test_project_exists_true(monkeypatch, tmp_path):
    p = tmp_path / 'oss-fuzz' / 'projects' / 'proj'
    p.mkdir(parents=True)
    monkeypatch.setattr(ofgo, 'BASE_DIR', str(tmp_path))
    assert ofgo.project_exists('proj')


def test_validate_model_missing_key(monkeypatch):
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    with pytest.raises(SystemExit):
        ofgo.validate_model('gpt-4o-mini', 1)

def test_validate_model_invalid_key(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY', 'BADKEY')
    ofgo.validate_model('gpt-4o-mini', 1)

def test_cli_default_invalid_email(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY', 'dummy')
    monkeypatch.setattr(sys, 'argv', ['prog', 'default', '--repo', 'https://github.com/x/y', '--email', 'bad-email'])
    with pytest.raises(SystemExit):
        ofgo.run_on_args()

def test_cli_pre_existing_not_found(monkeypatch, tmp_path):
    monkeypatch.setattr(ofgo, 'BASE_DIR', str(tmp_path))
    monkeypatch.setenv('OPENAI_API_KEY', 'dummy')
    monkeypatch.setattr(sys, 'argv', ['prog', 'pre-existing', '--project', 'missing'])
    with pytest.raises(ValueError):
        ofgo.run_on_args()

def test_cli_pre_existing_found(monkeypatch, tmp_path):
    root = tmp_path / 'oss-fuzz' / 'projects' / 'proj'
    root.mkdir(parents=True)
    monkeypatch.setattr(ofgo, 'BASE_DIR', str(tmp_path))
    monkeypatch.setenv('OPENAI_API_KEY', 'dummy')
    monkeypatch.setattr(ofgo.harness_gen, 'generate_harness', lambda *a, **kw: None)
    monkeypatch.setattr(ofgo, 'validate_model', lambda *a, **kw: None)
    monkeypatch.setattr(sys, 'argv', ['prog', 'pre-existing', '--project', 'proj'])
    ofgo.run_on_args()
