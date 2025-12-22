import pytest
import os
import shutil
import filecmp

from helpers import ensure_dir_exists
from harness_gen import setup_folder_syncing, sync_samples

BASE_DIR = os.path.dirname(__file__)
PYCACHE_DIR = os.path.join(BASE_DIR, "__pycache__")
TEST_FILE_DIR = os.path.join(BASE_DIR, "__pycache__", "test")
PROJECT_DIR = os.path.join(TEST_FILE_DIR, "project")
SAMPLES_DIR = os.path.join(TEST_FILE_DIR, "samples")
GEN_PROJECT_DIR = os.path.join(TEST_FILE_DIR, "gen-project")

def _write_string_to_file(directory, name, string):
    ensure_dir_exists(directory)
    output_path = os.path.join(directory, name)
    with open(output_path, "w") as f:
        f.write(string)

def _cleanup():
    if os.path.exists(TEST_FILE_DIR):
        shutil.rmtree(TEST_FILE_DIR)

def test_setup_folder_syncing_generated_nopreexisting():
    _write_string_to_file(GEN_PROJECT_DIR, "generated", "generated")
    setup_folder_syncing(GEN_PROJECT_DIR, PROJECT_DIR)
    assert filecmp.cmp(os.path.join(PROJECT_DIR, "generated"), os.path.join(GEN_PROJECT_DIR, "generated"))
    _write_string_to_file(PYCACHE_DIR, "generated", "generated")
    assert filecmp.cmp(os.path.join(PROJECT_DIR, "generated"), os.path.join(PYCACHE_DIR, "generated"))
    _cleanup()


def test_setup_folder_syncing_generated_preexisting():
    _write_string_to_file(GEN_PROJECT_DIR, "generated", "generated")
    _write_string_to_file(PROJECT_DIR, "preexisting", "preexisting")
    setup_folder_syncing(GEN_PROJECT_DIR, PROJECT_DIR)
    assert filecmp.cmp(os.path.join(PROJECT_DIR, "generated"), os.path.join(GEN_PROJECT_DIR, "generated"))
    _write_string_to_file(PYCACHE_DIR, "generated", "generated")
    assert filecmp.cmp(os.path.join(PROJECT_DIR, "generated"), os.path.join(PYCACHE_DIR, "generated"))
    _cleanup()

def test_setup_folder_syncing_nogenerated_preexisting():
    _write_string_to_file(PROJECT_DIR, "preexisting", "preexisting")
    setup_folder_syncing(GEN_PROJECT_DIR, PROJECT_DIR)
    assert filecmp.cmp(os.path.join(PROJECT_DIR, "preexisting"), os.path.join(GEN_PROJECT_DIR, "preexisting"))
    _write_string_to_file(PYCACHE_DIR, "preexisting", "preexisting")
    assert filecmp.cmp(os.path.join(PROJECT_DIR, "preexisting"), os.path.join(PYCACHE_DIR, "preexisting"))
    _cleanup()

def test_setup_folder_syncing_nogenerated_nopreexisting():
    with pytest.raises(SystemExit):
        setup_folder_syncing(GEN_PROJECT_DIR, PROJECT_DIR)
    _cleanup()

def _setup_samples():
    test_string = "test"
    _write_string_to_file(os.path.join(PROJECT_DIR, "argcomplete"), "argcomplete.txt", "argcomplete")
    _write_string_to_file(os.path.join(PROJECT_DIR, "anyio"), "anyio.txt", "anyio")
    _write_string_to_file(os.path.join(PROJECT_DIR, "argcomplete-argcomplete.finders.completionfinder._call-1"), "test.txt", test_string)
    _write_string_to_file(os.path.join(PROJECT_DIR, "argcomplete-argcomplete.finders.completionfinder.rl_complete-1"), "test.txt", test_string)
    _write_string_to_file(os.path.join(PROJECT_DIR, "anyio-anyio.core.sockets.connect_tcp-1"), "test.txt", test_string)
    _write_string_to_file(os.path.join(PROJECT_DIR, "anyio-anyio.to_process.run_sync-1"), "test.txt", test_string)
    _write_string_to_file(os.path.join(PROJECT_DIR, "jupyter_server-jupyter_server.auth.decorator.authorized.wrapper.inner-1"), "test.txt", test_string)
    _write_string_to_file(os.path.join(PROJECT_DIR, "jupyter_server-jupyter_server.services.contents.manager.asynccontentsmanager.copy-1"), "test.txt", test_string)

def test_sync_samples():
    _setup_samples()
    assert sync_samples(PROJECT_DIR, SAMPLES_DIR, "argcomplete")
    assert os.path.exists(os.path.join(SAMPLES_DIR, "argcomplete-argcomplete.finders.completionfinder._call-1"))
    assert os.path.exists(os.path.join(SAMPLES_DIR, "argcomplete-argcomplete.finders.completionfinder.rl_complete-1"))
    assert filecmp.cmp(os.path.join(SAMPLES_DIR, "argcomplete-argcomplete.finders.completionfinder._call-1", "test.txt"),
            os.path.join(PROJECT_DIR, "argcomplete-argcomplete.finders.completionfinder._call-1", "test.txt"))
    assert filecmp.cmp(os.path.join(SAMPLES_DIR, "argcomplete-argcomplete.finders.completionfinder.rl_complete-1", "test.txt"),
            os.path.join(PROJECT_DIR, "argcomplete-argcomplete.finders.completionfinder.rl_complete-1", "test.txt"))
    assert not os.path.exists(os.path.join(SAMPLES_DIR, "argcomplete"))
    assert not os.path.exists(os.path.join(SAMPLES_DIR, "anyio"))
    assert not os.path.exists(os.path.join(SAMPLES_DIR, "anyio-anyio.core.sockets.connect_tcp-1"))
    assert not os.path.exists(os.path.join(SAMPLES_DIR, "anyio-anyio.to_process.run_sync-1"))
    assert not os.path.exists(os.path.join(SAMPLES_DIR, "jupyter_server-jupyter_server.auth.decorator.authorized.wrapper.inner-1"))
    assert not os.path.exists(os.path.join(SAMPLES_DIR, "jupyter_server-jupyter_server.services.contents.manager.asynccontentsmanager.copy-1"))
    _cleanup()

def test_sync_samples_bad_project():
    _setup_samples()
    assert not sync_samples(PROJECT_DIR, SAMPLES_DIR, "clamav")
    assert not os.path.exists(os.path.join(SAMPLES_DIR, "argcomplete-argcomplete.finders.completionfinder._call-1"))
    assert not os.path.exists(os.path.join(SAMPLES_DIR, "argcomplete-argcomplete.finders.completionfinder.rl_complete-1"))
    assert not os.path.exists(os.path.join(SAMPLES_DIR, "argcomplete"))
    assert not os.path.exists(os.path.join(SAMPLES_DIR, "anyio"))
    assert not os.path.exists(os.path.join(SAMPLES_DIR, "anyio-anyio.core.sockets.connect_tcp-1"))
    assert not os.path.exists(os.path.join(SAMPLES_DIR, "anyio-anyio.to_process.run_sync-1"))
    assert not os.path.exists(os.path.join(SAMPLES_DIR, "jupyter_server-jupyter_server.auth.decorator.authorized.wrapper.inner-1"))
    assert not os.path.exists(os.path.join(SAMPLES_DIR, "jupyter_server-jupyter_server.services.contents.manager.asynccontentsmanager.copy-1"))
    _cleanup()