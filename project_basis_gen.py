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

'''
project_basis_gen.py
--------------------
Creates the Dockerfile, project.yaml, build.sh, (and empty skeleton harnesses) for a given github repository and maintainer email

Usage:
    import project_basis_gen 

    output_path = project_basis_gen.generate_project_basis(<repo_url>, <maintainer_email>, [--model <model>]

Notes:
    - Assumes you have followed the setup guide: USAGE.md
    - model defaults to 'gpt-4o-mini'
'''

import os
import sys
import yaml
import shutil
import subprocess
from logger_config import setup_logger
from helpers import *

# -------------------------------------------------------------------
# Logging functionality
# -------------------------------------------------------------------
logger = setup_logger(color_text(__name__, ANSI_LIGHT_PURPLE))
def log(msg):
    logger.info(msg)

# -------------------------------------------------------------------
# Runner execution 
# -------------------------------------------------------------------
def run_runner(repo_url: str, repo_name: str, model: str) -> str:
    '''
    Calls OSS-Fuzz-Gen's experimental/build_generator/runner.py in agent mode
    Return Value (path to generated files):
        OSS_FUZZ_GEN_DIR/generated-builds-tmp/oss-fuzz-projects/<repo_name>
    '''
    
    # Runner command expects repo name as a text file "input.txt"
    input_path = os.path.join(OSS_FUZZ_GEN_DIR, "input.txt")
    with open(input_path, 'w') as f:
        f.write(repo_url + "\n")
    
    # Get rid of previous temporary folder
    # If the program later crashes, debug info is available in this directory
    tmp_output_dir = os.path.join(OSS_FUZZ_GEN_DIR, "generated-builds-tmp")
    clean_dir(tmp_output_dir)

    cmd = [
        "python3", "-m", "experimental.build_generator.runner",
        "-i", input_path,
        "-o", "generated-builds-tmp",
        "-m", model,
        "--oss-fuzz", OSS_FUZZ_DIR,
        "-a",
    ]

    # Run the oss-fuzz-gen command to create the build files
    log(f"Running OSS-Fuzz-Gen for {repo_name} using model: {model}")
    try:
        subprocess.run(cmd, cwd=OSS_FUZZ_GEN_DIR, check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Runner failed with exit code {e.returncode}")

    # Locate the generated files
    projects_dir = os.path.join(tmp_output_dir, "oss-fuzz-projects")
    if not os.path.isdir(projects_dir) or not os.listdir(projects_dir):
        raise RuntimeError("No generated build directories found — check OSS-Fuzz-Gen output")
    
    # Find generated project names
    # We loop over any name starting with our repo name, in case of weird duplicate issues
    #   Should match repo name exactly
    dirs = os.listdir(projects_dir)
    if not dirs:
        raise RuntimeError("OSS-Fuzz-Gen produced no builds")
    candidates = [
        d for d in dirs if d.lower().startswith(repo_name)
    ]

    if not candidates:
        raise RuntimeError(
            f"No generated directory matched repo '{repo_name}'. Found OSS-Fuzz Projects: {dirs}. "
            f"Check {tmp_output_dir} for debug info."
        )
    
    # Should only be 1 existing
    chosen = candidates[0] 
    output_path = os.path.join(projects_dir, chosen)
    log(f"Generated project basis directory: {output_path}")

    return output_path 
# -------------------------------------------------------------------
# Copy and patch functions
# -------------------------------------------------------------------
def copy_outputs(src_dir: str, dst_dir: str) -> None:
    '''Entire entire project build dir to the dst directory.'''
    log(f"Copying files from {src_dir} to {dst_dir}")

    # dst_dir confirmed not to exist by main
    shutil.copytree(src_dir, dst_dir)
    files = os.listdir(dst_dir)
    log(f"Copied files: {files}")
    log(f"Copied: {files} to {dst_dir}")

def patch_project_yaml(yaml_path: str, email: str) -> None:
    '''Update the maintainer email in project.yaml.'''
    if not os.path.exists(yaml_path):
        log("project.yaml not found. skipping patch")
        return
    with open(yaml_path, 'r') as f:
        y = yaml.safe_load(f) or {}
    y['primary_contact'] = email
    with open(yaml_path, 'w') as f:
        yaml.dump(y, f, sort_keys=False)
    log(f"Updated maintainer email to: {email}")

# -------------------------------------------------------------------
# Main workflow
# -------------------------------------------------------------------
def generate_project_basis(repo_url: str, email: str, model: str = DEFAULT_MODEL) -> str:
    '''
    Calls function to generate the 3 basis files
    Copies the output out of oss-fuzz-gen and into out_dir.
    Patches the project.yaml with email as primary_contact
    '''
    
    # Grab repo name
    repo_name = sanitize_repo_name(repo_url)
    
    # Create gen-projects dir if it does not exist
    log(f"[+] Starting OSS-Fuzz basis generation for {repo_name}")
    if not os.path.exists(PERSISTENCE_DIR):
        os.makedirs(PERSISTENCE_DIR)


    # gen-projects/<repo_name>
    out_dir = os.path.join(PERSISTENCE_DIR, repo_name)

    # do not overwrite previous projects
    if os.path.exists(out_dir):
        log(f"Existing project at {out_dir}. Skipping generation")
        return out_dir

    # Call oss-fuzz-gen's 'runner' for build generation: Get the path of the generated files
    generated_dir = run_runner(repo_url, repo_name, model)


    # Copy output and patch yaml
    copy_outputs(generated_dir, out_dir)
    patch_project_yaml(os.path.join(out_dir, "project.yaml"), email)
    
    log(f"Generation complete for {repo_name}")
    log(f"Output saved under: {out_dir}")
    
    return out_dir
