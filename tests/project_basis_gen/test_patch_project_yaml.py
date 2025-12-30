import os
import shutil
import yaml
from project_agent_gen import patch_project_yaml

BASE_DIR = os.path.dirname(__file__)
TEST_FILE_DIR = os.path.join(BASE_DIR, "..", "temp_yaml")


def _write_string_to_file(directory, name, content):
    os.makedirs(directory, exist_ok=True)
    with open(os.path.join(directory, name), "w") as f:
        f.write(content)


def _setup():
    proj = os.path.join(TEST_FILE_DIR, "proj")
    os.makedirs(proj, exist_ok=True)
    yaml_path = os.path.join(proj, "project.yaml")
    _write_string_to_file(proj, "project.yaml", "primary_contact: old@example.com\n")
    return yaml_path


def _cleanup():
    if os.path.exists(TEST_FILE_DIR):
        shutil.rmtree(TEST_FILE_DIR)


def test_patch_project_yaml_updates_contact():
    yaml_path = _setup()
    patch_project_yaml(yaml_path, "new@example.com")

    with open(yaml_path) as f:
        loaded = yaml.safe_load(f)

    assert loaded["primary_contact"] == "new@example.com"
    _cleanup()


def test_patch_project_yaml_missing_ok():
    missing = os.path.join(TEST_FILE_DIR, "no_file.yaml")
    patch_project_yaml(missing, "whatever")

