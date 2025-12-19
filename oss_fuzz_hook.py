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

"""
OSS-Fuzz Runner
Will run existing or newly generated OSS-Fuzz harnesses
"""
import os
import subprocess
import re

from logger_config import setup_logger
from helpers import BASE_DIR, OSS_FUZZ_DIR

logger = setup_logger()
## Purple
def log(output):
    logger.info(f"\033[95moss_fuzz_hook:\033[00m {output}")

"""
Runs OSS-Fuzz projects with either existing or generated harnesses

Args:
    project (str): Name of the project to run with oss-fuzz. Required.
    harness_type (str): Choose whether to run existing harness in oss-fuzz or generated harnesses. Default to "existing".

Returns (bool): Success/Failure status 
"""
def run_project(project: str = None, harness_type: str = "existing"):
    """
    Run OSS-Fuzz project with specified harness type.
    
    Args:
        project: The project name
        harness_type: "existing" for standard OSS-Fuzz harnesses, 
                     "generated" for automatically generated harnesses
    """
    path_to_helper = os.path.join(OSS_FUZZ_DIR, "infra", "helper.py")
    
    if harness_type == "existing":
        log(f"Running existing project {project} with OSS-FUZZ.")
    elif harness_type == "generated":
        log(f"Running generated project {project} with OSS-FUZZ.")
    else:
        log(f"Error: Unknown harness_type '{harness_type}'. Use 'existing' or 'generated'.")
        return False
    
    # Build the project (same for both types)
    commands = [
        ["python3", path_to_helper, "pull_images"],
        ["python3", path_to_helper, "build_image", project, "--pull"],
        ["python3", path_to_helper, "build_fuzzers", project]
    ]
    for c in commands:
        log(f"Building images for {project}")
        if c == ["python3", path_to_helper, "build_image", project]:
            res = subprocess.run(c, input="y\n", text=True)
        else:
            res = subprocess.run(c)
        if res.returncode != 0:
            log(f"Error: {res.stderr}")
            return False
        else:
            log(f"Success: {c}")
    
    path_to_fuzzers = os.path.join(OSS_FUZZ_DIR, "build", "out", project)
    if not os.path.exists(path_to_fuzzers):
        log(f"Fuzzers directory not found: {path_to_fuzzers}")
        return False
    
    if harness_type == "existing":
        # Look for typical OSS-Fuzz harness pattern: fuzz_* or *Fuzzer
        fuzzers = []
        for i in os.listdir(path_to_fuzzers):
            if i.startswith("fuzz_") or i.endswith("Fuzzer") or re.match(r'^fuzz-harness-\d+_\d+\$', i) and '.' not in i:
                fuzzers.append(i)
        
        if len(fuzzers) == 0:
            log("Error: No existing fuzzers found with pattern 'fuzz_*'.")
            return False
        
        log(f"Found {len(fuzzers)} fuzzers for {project}")
        for fuzz in fuzzers:
            result = subprocess.run(["python3", path_to_helper, "run_fuzzer", project, fuzz, "--", "-max_total_time=600", "-runs=1000"])
            if result.returncode == 0:
                log(f"{fuzz} completed successfully")
            else:
                log(f"{fuzz} failed")
        return True
        
    elif harness_type == "generated":
        generated_fuzzers = []
        for i in os.listdir(path_to_fuzzers):
            # Match pattern: fuzz-harness-{sample_num}_{fuzz_target_num}
            if re.match(r'^fuzz-harness-\d+_\d+\$', i) and '.' not in i:
                generated_fuzzers.append(i)
        
        if not generated_fuzzers:
            log("Error: No generated fuzzers found with pattern 'fuzz-harness-{sample}_{target}'.")
            return False
        
        log(f"Found {len(generated_fuzzers)} generated fuzzers: {generated_fuzzers}")
        
        # Run all generated harnesses
        success_count = 0
        for fuzzer in generated_fuzzers:
            log(f"Running generated fuzzer: {fuzzer}")
            result = subprocess.run([
                "python3", path_to_helper, "run_fuzzer", project, fuzzer, "--", "-max_total_time=600", "-runs=1000"
            ])
            if result.returncode == 0:
                success_count += 1
                log(f"{fuzzer} completed successfully")
            else:
                log(f"{fuzzer} failed")
        
        log(f"Completed running {success_count}/{len(generated_fuzzers)} generated fuzzers")
        return True