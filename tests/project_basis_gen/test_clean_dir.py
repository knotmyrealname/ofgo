import os
import shutil
import pytest
from project_agent_gen import clean_dir

BASE_DIR = os.path.dirname(__file__)
TEST_FILE_DIR = os.path.join(BASE_DIR, "..", "temp_clean_dir")


def _write_string_to_file(directory, name, content):
    os.makedirs(directory, exist_ok=True)
    with open(os.path.join(directory, name), "w") as f:
        f.write(content)


def _setup():
    os.makedirs(TEST_FILE_DIR, exist_ok=True)

    # file
    _write_string_to_file(TEST_FILE_DIR, "file.txt", "hello")

    # directory
    os.makedirs(os.path.join(TEST_FILE_DIR, "dir"), exist_ok=True)

    # symlink
    target = os.path.join(TEST_FILE_DIR, "symlink_target")
    os.makedirs(target, exist_ok=True)
    link = os.path.join(TEST_FILE_DIR, "link")
    if not os.path.exists(link):
        os.symlink(target, link)


def _cleanup():
    if os.path.exists(TEST_FILE_DIR):
        shutil.rmtree(TEST_FILE_DIR)


def test_clean_dir_file():
    _setup()
    f = os.path.join(TEST_FILE_DIR, "file.txt")
    assert os.path.exists(f)
    clean_dir(f)
    assert not os.path.exists(f)
    _cleanup()


def test_clean_dir_directory():
    _setup()
    d = os.path.join(TEST_FILE_DIR, "dir")
    assert os.path.isdir(d)
    clean_dir(d)
    assert not os.path.exists(d)
    _cleanup()


def test_clean_dir_symlink():
    _setup()
    l = os.path.join(TEST_FILE_DIR, "link")
    assert os.path.islink(l)
    clean_dir(l)
    assert not os.path.exists(l)
    _cleanup()


def test_clean_dir_missing_does_not_fail():
    clean_dir(os.path.join(TEST_FILE_DIR, "does_not_exist"))

