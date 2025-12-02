import pytest
import os
import shutil
import logging
from helpers import ensure_dir_exists
from harness_gen import get_ext_from_project

BASE_DIR = os.path.dirname(__file__)
TEST_FILE_DIR = os.path.join(BASE_DIR, ".." , "temp")
LOGGER = logging.getLogger(__name__)

def _write_string_to_file(directory, name, string):
    ensure_dir_exists(directory)
    output_path = os.path.join(directory, name)
    with open(output_path, "w") as f:
        f.write(string)

def _cleanup():
    if os.path.exists(TEST_FILE_DIR):
        shutil.rmtree(TEST_FILE_DIR)

def test_get_ext_from_project_python():
    yaml = '''## Project homepage
homepage: https://github.com/plotly/dash

## Project language
language: python

## Primary contact and list of contacts to be CC-ed for bugs - requires Google account
primary_contact: ddong2@ncsu.edu
auto_ccs:

## Path to repository hosting source code
main_repo: https://github.com/plotly/dash

## (OPT) List of vendor (downstream consumer) email addresses that want access to bug reports as they are filed
vendor_ccs: 

## (OPT) List of sanitizers to use. (Options: address, memory, undefined).
sanitizers:
- address
- undefined

## (OPT) List of architectures to fuzz on (Options: x86_64, i386). x86_64 is used by default
architectures:
- x86_64

## (OPT) List of fuzzing engines to use - libfuzzer is required. By default, libfuzzer, afl, honggfuzz, and centipede are used.
fuzzing_engines:
- libfuzzer

## (OPT) Link to a custom help URL that can appear instead of the default guide
help_url:

## (OPT) Number of builds per day (Once per day by default, with a cap of 4 builds per day)
builds_per_day: 1
'''

    _write_string_to_file(TEST_FILE_DIR, "project.yaml", yaml)
    assert "py" == get_ext_from_project(TEST_FILE_DIR)
    _cleanup()

def test_get_ext_from_project_cpp():
    yaml = '''homepage: "https://www.clamav.net/"
language: c++
primary_contact: "clamav.fuzz@gmail.com"
auto_ccs:
    - clamav-bugs@external.cisco.com
sanitizers:
 - address
 - undefined
fuzzing_engines:
 - libfuzzer
 - afl
main_repo: 'https://github.com/Cisco-Talos/clamav-devel.git'
'''

    _write_string_to_file(TEST_FILE_DIR, "project.yaml", yaml)
    assert "cpp" == get_ext_from_project(TEST_FILE_DIR)
    _cleanup()

def test_get_ext_from_project_nonexistent(caplog):
    yaml = '''homepage: "https://www.clamav.net/"
language:
primary_contact: "clamav.fuzz@gmail.com"
auto_ccs:
    - clamav-bugs@external.cisco.com
sanitizers:
 - address
 - undefined
fuzzing_engines:
 - libfuzzer
 - afl
main_repo: 'https://github.com/Cisco-Talos/clamav-devel.git'
'''

    _write_string_to_file(TEST_FILE_DIR, "project.yaml", yaml)
    ## Leaving this in here, but it seems as if the log message can't be checked
    with pytest.raises(SystemExit):
        with caplog.at_level(logging.INFO):
            get_ext_from_project(TEST_FILE_DIR)
        assert "Unable to identify language" in caplog.text
    _cleanup()
    
def test_get_ext_from_project_bad_language():
    yaml = '''homepage: "https://www.clamav.net/"
language: psython
primary_contact: "clamav.fuzz@gmail.com"
auto_ccs:
    - clamav-bugs@external.cisco.com
sanitizers:
 - address
 - undefined
fuzzing_engines:
 - libfuzzer
 - afl
main_repo: 'https://github.com/Cisco-Talos/clamav-devel.git'
'''

    _write_string_to_file(TEST_FILE_DIR, "project.yaml", yaml)
    with pytest.raises(SystemExit):
        get_ext_from_project(TEST_FILE_DIR)
    _cleanup()

def test_get_ext_from_project_bad_yaml():
    yaml = '''homepage: "https://www.clamav.net/"
language: 
 - c++
primary_contact: "clamav.fuzz@gmail.com"
auto_ccs:
    - clamav-bugs@external.cisco.com
sanitizers:
 - address
 - undefined
fuzzing_engines:
 - libfuzzer
 - afl
main_repo: 'https://github.com/Cisco-Talos/clamav-devel.git'
'''

    _write_string_to_file(TEST_FILE_DIR, "project.yaml", yaml)
    with pytest.raises(SystemExit):
        get_ext_from_project(TEST_FILE_DIR)
    _cleanup()