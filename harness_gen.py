#!/usr/bin/env python3
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import os
import re
import time
import subprocess
import shutil

sys.path.insert(0, "./oss-fuzz-gen")
import run_all_experiments
from helpers import *

## Variable declaration
BENCHMARK_HEURISTICS = "far-reach-low-coverage,low-cov-with-fuzz-keyword,easy-params-far-reach"
NUMBER_OF_HARNESSES = 2
NUM_SAMPLES = 1 # Currently only supports 1 - may lead to unexpected behavior
RESULTS_DIR = os.path.join(BASE_DIR, "results")
REPORT_DIR = os.path.join(BASE_DIR, "report")
GENERATED_SAMPLES_DIR = os.path.join(PERSISTENCE_DIR, "SAMPLES")

logger = setup_logger(color_text(__name__, ANSI_CYAN))
def log(msg):
    logger.info(msg)
def err(msg):
    logger.error(color_text(msg, ANSI_RED))
    sys.exit(1)

def get_ext_from_project(project_dir: str) -> str:
    """Determines the file extension for a project based on its language.
    
    Reads the project.yaml file to identify the language and returns the
    corresponding file extension. If the language is unsupported, exits with error.

    Args:
        project_dir (str): Path to the project directory.
    
    Returns:
        str: The file extension corresponding to the project's language.

    Raises:
        SystemExit: If the language cannot be identified or is not supported.
    """
    project_yaml = os.path.join(project_dir, "project.yaml")

    language = ''
    with open(project_yaml, 'r') as f:
        yaml_content = f.read().splitlines()
        for line in yaml_content:
            if line.startswith('language:'):
                language = line.split(':', 1)[1].strip()

    try:
        check_language_support(language)
        return LANGUAGE_EXTS[language]
    except ValueError as ve:
        err(f"ValueError: {ve}.\n Ensure your project.yaml is in oss-fuzz/projects and has a properly configured project.yaml.")

def clean_old_harnesses(project_dir: str) -> None:
    """Removes old generated harnesses for a given project.
    
    Searches for and deletes files matching the pattern 'fuzz_harness-DD_DD.*'
    where DD represents digits.

    Args:
        project_dir (str): Path to the project directory to clean up.
    """
    log("Cleaning old harnesses")
    old_fuzz_target_regex = fr'fuzz_harness-\d\d_\d\d.(.)*'
    for root, dirs, files in os.walk(project_dir):
        for name in files:
            if re.match(old_fuzz_target_regex, name):
                os.remove(os.path.join(project_dir, name))

def setup_folder_syncing(priority_project_dir: str, secondary_project_dir: str) -> None:
    """Sets up folder syncing between two directories.
    
    Prioritizes syncing the first directory to the secondary directory if it exists. 
    If it doesn't, it tries syncing the secondary directory to the first. This ensures
    that the project folders are up to date.

    Args:
        priority_project_dir (str): Path to the prioritized project directory (usually OFGO-generated).
        secondary_project_dir (str): Path to the secondary project directory (usually OSS-Fuzz).
    
    Raises:
        SystemExit: If neither directory exists.
    """
    if os.path.exists(priority_project_dir): ## Prioritize our generated projects over existing projects
        log("Found OFGO-Generated project. Proceeding with Generation.")
        sync_dirs(priority_project_dir, secondary_project_dir)
    elif os.path.exists(secondary_project_dir):
        log("Found pre-existing OSS-Fuzz project. Proceeding with Generation.")
        sync_dirs(secondary_project_dir, priority_project_dir)
    else:
        err(f"Cannot find Project folder at {secondary_project_dir} or any generated projects.")

def cleanup_samples(samples_dir: str, project: str) -> None:
    """Removes generated sample directories for a given project.
    
    Searches for and deletes directories matching the pattern 'project-.*-\\d*'.

    Args:
        samples_dir (str): Path to the directory to clean samples in.
        project (str): Name of the project to clean up samples for.
    """
    generated_project_regex = fr'{project}-.*-\d*'
    for root, dirs, files in os.walk(samples_dir):
        for name in dirs:
            if re.match(generated_project_regex, name):
                shutil.rmtree(os.path.join(samples_dir, name))


def sync_samples(projects_dir: str, samples_dir: str, project: str) -> bool:
    """Syncs generated harness samples to the samples directory.
    
    Searches for directories matching the pattern 'project-.*-\\d*' in the OSS-Fuzz
    projects directory and syncs them to the samples directory.

    Args:
        projects_dir (str): Path to the projects directory.
        samples_dir (str): Path to the samples directory.
        project (str): Name of the project.
    
    Returns:
        bool: True if output was found and synced, False otherwise.
    """
    generated_project_regex = fr'{project}-.*-\d*'
    found_output = False
    for root, dirs, files in os.walk(projects_dir):
        for name in dirs:
            if re.match(generated_project_regex, name):
                found_output = True
                harness_dir = os.path.join(projects_dir, name)
                target_dir = os.path.join(samples_dir, name)
                sync_dirs(harness_dir, target_dir)
    return found_output

def validate_project(project_dir: str) -> None:
    """Validates that a project directory contains required files.
    
    Checks that the project directory contains a build.sh, project.yaml, and Dockerfile.

    Args:
        project_dir (str): Path to the project directory to validate.
    
    Raises:
        SystemExit: If any required files are missing.
    """
    required_items = ["build.sh", "project.yaml", "Dockerfile"]
    for root, dirs, files in os.walk(project_dir):
        for name in files:
            for item in required_items:
                if name == item:
                    required_items.remove(item)
    if len(required_items) != 0:
        err(f"Project at {project_dir} missing either a project.yaml, Dockerfile, or build.sh. Please add the missing file.")

def generate_harness(model: str, project: str, temperature: float = DEFAULT_TEMPERATURE) -> bool:
    """Generates OSS-Fuzz-gen harnesses for a given project.
    
    Uses the specified LLM model and temperature to generate fuzz harnesses.
    Manages project directories, runs the generation pipeline, and syncs results
    to the persistent samples (gen-projects) directory.

    Args:
        model (str): The LLM model to use for harness generation.
        project (str): The project name (expects project folder to either be in 'ofgo/gen-projects' 
            or 'ofgo/oss-fuzz/projects').
        temperature (str): The temperature setting for the model. Defaults to DEFAULT_TEMPERATURE.

    Returns:
        bool: True if harness generation succeeded, False otherwise.
    """ 
    ## Sets up synced folders for persistence
    persistent_project_dir = os.path.join(PERSISTENCE_DIR, project)
    project_dir = os.path.join(OSS_FUZZ_PROJECTS_DIR, project)

    ensure_dir_exists(GENERATED_SAMPLES_DIR)
    setup_folder_syncing(persistent_project_dir, project_dir)
    validate_project(persistent_project_dir)
        
    ## Cleans up samples
    cleanup_samples(GENERATED_SAMPLES_DIR, project)
    cleanup_samples(OSS_FUZZ_PROJECTS_DIR, project)
    clean_old_harnesses(project_dir)
    sync_dirs(project_dir, persistent_project_dir)

    log("Beginning OSS-Fuzz-gen harness generation. This may take a long time")
    start = time.time()

    ## Set up OSS-Fuzz-gen working directories
    ensure_dir_exists(WORK_DIR)
    
    ## Runs OSS-Fuzz-gen with custom params
    script = os.path.join(SCRIPTS_DIR, "ofgo-scripts", "run-project-modified.sh")
    subprocess.run(["chmod", "+x", script])
    subprocess.run([script,
                   OSS_FUZZ_GEN_DIR,
                   OSS_FUZZ_DIR,
                   INTROSPECTOR_DIR,
                   BENCHMARK_HEURISTICS,
                   project,
                   str(NUMBER_OF_HARNESSES),
                   str(NUM_SAMPLES),
                   model,
                   str(temperature),
                   RESULTS_DIR])

    end = time.time()
    log("Completed in %.4f seconds" % (end - start))

    ## Sync generated data to a folder outside oss-fuzz for persistence
    found_output = sync_samples(OSS_FUZZ_PROJECTS_DIR, GENERATED_SAMPLES_DIR, project)
                
    if found_output:
        log(f"Your generated harnesses can be found in {project}-{project}..." +
                    "as XX.fuzz_target. To use them, you can move them to your main folder and rename them.")

        ## Get report from OSS-Fuzz-gen run
        os.chdir(OSS_FUZZ_GEN_DIR)
        subprocess.run(["python","-m", "report.web", "-r", RESULTS_DIR, "-o", REPORT_DIR])
        log(f"Report Generated in {REPORT_DIR}")
        log(f"""To view the report, either open up the index.html located within in your web browser or run the command:
        python -m http.server -b 127.0.0.1 5000 -d {REPORT_DIR}""")
        log("You may have to change the IP address (127.0.0.1) or port (5000) to suit your needs.")
        return True
    else: 
        log("Generation Failed. You may have to check the run logs to diagnose the issue.")
        return False

def consolidate_harnesses(project: str, sample_num: int = 1) -> None:
    """Consolidates generated harnesses into a single directory.
    
    Retrieves generated harnesses for a project and consolidates them into
    the gen-projects directory outside of oss-fuzz.

    Args:
        project (str): The OSS-Fuzz project name to consolidate harnesses for.
        sample_num (int): The sample number to consolidate. Defaults to 1.
    """
    ## Check if the project exists
    project_dir = os.path.join(OSS_FUZZ_PROJECTS_DIR, project)
    if not os.path.exists(project_dir):
        log(f"Cannot locate project for consolidation at {project_dir}")
        return
    
    ensure_dir_exists(PERSISTENCE_DIR)
    persistent_project_dir = os.path.join(PERSISTENCE_DIR, project)
    
    ## Clean up prevous fuzz targets
    clean_old_harnesses(project)

    file_ext = get_ext_from_project(project_dir)

    ## Tries to copy over generated files for a specific run sample
    generated_project_regex = fr'{project}-.*-\d*'
    num_found = 1
    for root, dirs, files in os.walk(GENERATED_SAMPLES_DIR):
        for name in dirs:
            if re.match(generated_project_regex, name):
                source_file = os.path.join(GENERATED_SAMPLES_DIR, name, "%02d.fuzz_target" % (sample_num))
                dest_file = os.path.join(project_dir, "fuzz_harness-%02d_%02d.%s" % (sample_num, num_found, file_ext))
                shutil.copyfile(source_file, dest_file)
                num_found += 1

    sync_dirs(project_dir, persistent_project_dir)