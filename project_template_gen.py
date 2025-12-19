import os
import re
import sys
import git
import shutil
import filecmp
import subprocess
import ofgo
from pathlib2 import Path
from datetime import date
from logger_config import setup_logger
from helpers import *

logger = setup_logger()
def log(output): ## Green rep
    logger.info(f"\033[94mproject_template_gen:\033[00m {output}")

def generate_from_templates(repo_url: str, email: str, language: str, model: str):
    log("Generating Config Files from Template")
    ## Set up working directories
    if not os.path.exists(TARGET_REPO_DIR):
        os.makedirs(TARGET_REPO_DIR)
    if not os.path.exists(PERSISTENCE_DIR):
        os.makedirs(PERSISTENCE_DIR)

    project_name = validate_repo_url(repo_url)

    ## If the project exists in the gen-projects: test, don't generate
    persistent_project_dir = os.path.join(PERSISTENCE_DIR, project_name)
    if os.path.exists(persistent_project_dir):
        log(f"Project already exists at {persistent_project_dir}.")
        check_project_compilation(project_name)
    else:
        create_new_project(repo_url, email, project_name, language)

def create_new_project(repo_url: str, email: str, project_name: str, language: str):
    persistent_project_dir = os.path.join(PERSISTENCE_DIR, project_name)
    project_dir = os.path.join(OSS_FUZZ_DIR, "projects", project_name)
    
    log(f"Generating new project at {persistent_project_dir}.")
    template = os.path.join(TEMPLATE_DIR, language)
    if not os.path.exists(template):
        log(f"The language {language} is not yet supported by OSS-Fuzz.")
        sys.exit(1)
    ## Assume content is a placeholder if there's only one file.
    ## A blank folder shouldn't be possible in production, but we'll add the case just in case
    if len(os.listdir(template)) <= 1:
        log(f"Sorry. Templates for {language} have not been implemented yet.")
        sys.exit(1)

    ## Move over all files to new directory
    log(f"Generating templates at {persistent_project_dir}")
    shutil.copytree(template, persistent_project_dir)

    ## Fill out project.yaml
    yaml_template = os.path.join(persistent_project_dir, "project.yaml")
    if not os.path.exists(yaml_template):
        log(f"Project yaml does not exist in {template}. Skipping.")
    file = Path(yaml_template)
    yaml = file.read_text()
    yaml = yaml.replace("{repo}", repo_url)
    yaml = yaml.replace("{email}", email)
    file.write_text(yaml)

    ## Fill out Dockerfile
    dockerfile_template = os.path.join(persistent_project_dir, "Dockerfile")
    if not os.path.exists(dockerfile_template):
        log(f"Dockerfile does not exist in {template}. Skipping.")
    current_year = str(date.today().year)
    file = Path(dockerfile_template)
    dockerfile = file.read_text()
    dockerfile = dockerfile.replace("{repo}", repo_url)
    dockerfile = dockerfile.replace("{name}", project_name)
    dockerfile = dockerfile.replace("{year}", current_year)
    file.write_text(dockerfile)

    ## Fill out build.sh
    build_template = os.path.join(persistent_project_dir, "build.sh")
    if not os.path.exists(build_template):
        log(f"build.sh does not exist in {template}. Skipping.")
    file = Path(build_template)
    build = file.read_text()
    build = build.replace("{year}", current_year)
    file.write_text(build)
        
    log("Project Config Generated. Warning: Some Config files may require further editing to be functional. This is especially true for " + 
        "projects that have many dependency requirements. After updating the config, either rerun TEMPLATE gen with the same parameters or run \n    " + 
        f"python3 ofgo.py existing --project {project_name} --model <yourmodel> --temperature <yourtemperature>")
    
    ## Exits on the creation of a template as the user needs to update it.
    log(r"WARNING: Make sure that you update the harness (indicated by fuzz_test.{ext}) to be at least " +
        "a minimal fuzz harness - the Fuzz Introspector cannot do its job without some coverage, meaning no " +
        "functions can be selected for harness generation.")

    sys.exit(1)
    
    
