import pytest
import os
import shutil

from helpers import ensure_dir_exists
from harness_gen import clean_old_harnesses, cleanup_samples

BASE_DIR = os.path.dirname(__file__)
TEST_FILE_DIR = os.path.join(BASE_DIR, "__pycache__", "test")
PROJECT_DIR = os.path.join(TEST_FILE_DIR, "project")
SAMPLES_DIR = os.path.join(TEST_FILE_DIR, "samples")

def _write_string_to_file(directory, name, string):
    ensure_dir_exists(directory)
    output_path = os.path.join(directory, name)
    with open(output_path, "w") as f:
        f.write(string)

def _setup_clean_old_harnesses():
    test_string = "test"
    _write_string_to_file(PROJECT_DIR, "build.sh", test_string)
    _write_string_to_file(PROJECT_DIR, "Dockerfile", test_string)
    _write_string_to_file(PROJECT_DIR, "project.yaml", test_string)
    _write_string_to_file(PROJECT_DIR, "fuzz_test.py", test_string)
    _write_string_to_file(PROJECT_DIR, "fuzz_test.cpp", test_string)
    _write_string_to_file(PROJECT_DIR, "fuzz_harness-01.py", test_string)
    _write_string_to_file(PROJECT_DIR, "fuzz_harness-01_01.py", test_string)
    _write_string_to_file(PROJECT_DIR, "fuzz_harness-01_02.py", test_string)
    _write_string_to_file(PROJECT_DIR, "fuzz_harness-02_01.py", test_string)
    _write_string_to_file(PROJECT_DIR, "fuzz_harness-02_02.py", test_string)
    _write_string_to_file(PROJECT_DIR, "fuzz_harness-01_01.cpp", test_string)
    _write_string_to_file(PROJECT_DIR, "fuzz_harness-01_02.cpp", test_string)
    _write_string_to_file(PROJECT_DIR, "fuzz_harness-02_01.cpp", test_string)
    _write_string_to_file(PROJECT_DIR, "fuzz_harness-02_02.cpp", test_string)

def _cleanup():
    if os.path.exists(TEST_FILE_DIR):
        shutil.rmtree(TEST_FILE_DIR)

def test_clean_old_harnesses_buildsh():
    _setup_clean_old_harnesses()
    clean_old_harnesses(PROJECT_DIR)
    assert os.path.exists(os.path.join(PROJECT_DIR, "build.sh"))
    _cleanup()

def test_clean_old_harnesses_yaml():
    _setup_clean_old_harnesses()
    clean_old_harnesses(PROJECT_DIR)
    assert os.path.exists(os.path.join(PROJECT_DIR, "project.yaml"))
    _cleanup()

def test_clean_old_harnesses_dockerfile():
    _setup_clean_old_harnesses()
    clean_old_harnesses(PROJECT_DIR)
    assert os.path.exists(os.path.join(PROJECT_DIR, "Dockerfile"))
    _cleanup()

def test_clean_old_harnesses_regular_fuzzer_py():
    _setup_clean_old_harnesses()
    clean_old_harnesses(PROJECT_DIR)
    assert os.path.exists(os.path.join(PROJECT_DIR, "fuzz_test.py"))
    _cleanup()

def test_clean_old_harnesses_regular_fuzzer_cpp():
    _setup_clean_old_harnesses()
    clean_old_harnesses(PROJECT_DIR)
    assert os.path.exists(os.path.join(PROJECT_DIR, "fuzz_test.cpp"))
    _cleanup()

def test_clean_old_harnesses_modifiedgen_fuzzer_py():
    _setup_clean_old_harnesses()
    clean_old_harnesses(PROJECT_DIR)
    assert os.path.exists(os.path.join(PROJECT_DIR, "fuzz_harness-01.py"))
    _cleanup()

def test_clean_old_harnesses_gen_fuzzer_py():
    _setup_clean_old_harnesses()
    clean_old_harnesses(PROJECT_DIR)
    assert not os.path.exists(os.path.join(PROJECT_DIR, "fuzz_harness-01_01.py"))
    assert not os.path.exists(os.path.join(PROJECT_DIR, "fuzz_harness-01_02.py"))
    assert not os.path.exists(os.path.join(PROJECT_DIR, "fuzz_harness-02_01.py"))
    assert not os.path.exists(os.path.join(PROJECT_DIR, "fuzz_harness-02_02.py"))
    _cleanup()

def test_clean_old_harnesses_gen_fuzzer_cpp():
    _setup_clean_old_harnesses()
    clean_old_harnesses(PROJECT_DIR)
    assert not os.path.exists(os.path.join(PROJECT_DIR, "fuzz_harness-01_01.cpp"))
    assert not os.path.exists(os.path.join(PROJECT_DIR, "fuzz_harness-01_02.cpp"))
    assert not os.path.exists(os.path.join(PROJECT_DIR, "fuzz_harness-02_01.cpp"))
    assert not os.path.exists(os.path.join(PROJECT_DIR, "fuzz_harness-02_02.cpp"))
    _cleanup()


def _setup_cleanup_samples():
    test_string = "test"
    _write_string_to_file(os.path.join(SAMPLES_DIR, "argcomplete-argcomplete.finders.completionfinder._call-1"), "test.txt", test_string)
    _write_string_to_file(os.path.join(SAMPLES_DIR, "argcomplete-argcomplete.finders.completionfinder.rl_complete-1"), "test.txt", test_string)
    _write_string_to_file(os.path.join(SAMPLES_DIR, "anyio-anyio.core.sockets.connect_tcp-1"), "test.txt", test_string)
    _write_string_to_file(os.path.join(SAMPLES_DIR, "anyio-anyio.to_process.run_sync-1"), "test.txt", test_string)
    _write_string_to_file(os.path.join(SAMPLES_DIR, "jupyter_server-jupyter_server.auth.decorator.authorized.wrapper.inner-1"), "test.txt", test_string)
    _write_string_to_file(os.path.join(SAMPLES_DIR, "jupyter_server-jupyter_server.services.contents.manager.asynccontentsmanager.copy-1"), "test.txt", test_string)

def test_cleanup_samples_argcomplete():
    _setup_cleanup_samples()
    cleanup_samples(SAMPLES_DIR, "argcomplete")
    assert not os.path.exists(os.path.join(SAMPLES_DIR, "argcomplete-argcomplete.finders.completionfinder._call-1"))
    assert not os.path.exists(os.path.join(SAMPLES_DIR, "argcomplete-argcomplete.finders.completionfinder.rl_complete-1"))
    assert os.path.exists(os.path.join(SAMPLES_DIR, "anyio-anyio.core.sockets.connect_tcp-1"))
    assert os.path.exists(os.path.join(SAMPLES_DIR, "anyio-anyio.to_process.run_sync-1"))
    assert os.path.exists(os.path.join(SAMPLES_DIR, "jupyter_server-jupyter_server.auth.decorator.authorized.wrapper.inner-1"))
    assert os.path.exists(os.path.join(SAMPLES_DIR, "jupyter_server-jupyter_server.services.contents.manager.asynccontentsmanager.copy-1"))
    _cleanup()

def test_cleanup_samples_anyio():
    _setup_cleanup_samples()
    cleanup_samples(SAMPLES_DIR, "anyio")
    assert os.path.exists(os.path.join(SAMPLES_DIR, "argcomplete-argcomplete.finders.completionfinder._call-1"))
    assert os.path.exists(os.path.join(SAMPLES_DIR, "argcomplete-argcomplete.finders.completionfinder.rl_complete-1"))
    assert not os.path.exists(os.path.join(SAMPLES_DIR, "anyio-anyio.core.sockets.connect_tcp-1"))
    assert not os.path.exists(os.path.join(SAMPLES_DIR, "anyio-anyio.to_process.run_sync-1"))
    assert os.path.exists(os.path.join(SAMPLES_DIR, "jupyter_server-jupyter_server.auth.decorator.authorized.wrapper.inner-1"))
    assert os.path.exists(os.path.join(SAMPLES_DIR, "jupyter_server-jupyter_server.services.contents.manager.asynccontentsmanager.copy-1"))
    _cleanup()

def test_cleanup_samples_jupyter_server():
    _setup_cleanup_samples()
    cleanup_samples(SAMPLES_DIR, "jupyter_server")
    assert os.path.exists(os.path.join(SAMPLES_DIR, "argcomplete-argcomplete.finders.completionfinder._call-1"))
    assert os.path.exists(os.path.join(SAMPLES_DIR, "argcomplete-argcomplete.finders.completionfinder.rl_complete-1"))
    assert os.path.exists(os.path.join(SAMPLES_DIR, "anyio-anyio.core.sockets.connect_tcp-1"))
    assert os.path.exists(os.path.join(SAMPLES_DIR, "anyio-anyio.to_process.run_sync-1"))
    assert not os.path.exists(os.path.join(SAMPLES_DIR, "jupyter_server-jupyter_server.auth.decorator.authorized.wrapper.inner-1"))
    assert not os.path.exists(os.path.join(SAMPLES_DIR, "jupyter_server-jupyter_server.services.contents.manager.asynccontentsmanager.copy-1"))
    _cleanup()