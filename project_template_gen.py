import os
import sys
import git
import shutil
import filecmp
from pathlib2 import Path
from datetime import date
from logger_config import setup_logger

BASE_DIR = os.path.dirname(__file__)
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
TARGET_REPO_DIR = os.path.join(BASE_DIR, "work", "ofgo", "repositories")
PERSISTENCE_DIR = os.path.join(BASE_DIR, "gen-projects")

logger = setup_logger(__name__)
def log(output): ## Green rep
    logger.info(f"\033[94mproject_template_gen:\033[00m {output}")

def sanitize_repo_name(repo_url: str) -> str:
    """Extracts an OSS-Fuzz project name (lowercase repo name)."""
    name = os.path.basename(repo_url).replace(".git", "").strip().lower()
    if not name:
        raise ValueError(f"Could not parse repository name from URL: {repo_url}")
    return name

def generate_from_templates(repo_url: str, email: str, language: str, model: str):
    log("Generating Config Files from Template")
    ## Set up working directories
    if not os.path.exists(TARGET_REPO_DIR):
        os.makedirs(TARGET_REPO_DIR)
    if not os.path.exists(PERSISTENCE_DIR):
        os.makedirs(PERSISTENCE_DIR)

    ## Check to make sure repo is valid
    project_name = sanitize_repo_name(repo_url)
    try:
        project_repo_dir = os.path.join(TARGET_REPO_DIR, project_name)
        if os.path.exists(project_repo_dir):
            shutil.rmtree(project_repo_dir)
        git.Repo.clone_from(repo_url, project_repo_dir)
    except git.exc.GitError as e:
        log(f"ERROR! {repo_url} does not exist: \n{e}")
        sys.exit(1)

    ## Do not overwrite previous work
    project_dir = os.path.join(PERSISTENCE_DIR, project_name)

    if os.path.exists(project_dir):
        log(f"Project already exists at {project_dir}.")
    else:
        log(f"Generating new project at {project_dir}.")
        template = os.path.join(TEMPLATE_DIR, language)
        if not os.path.exists(template):
            log(f"The language {language} is not supported by OSS-Fuzz.")
            sys.exit(1)
        if len(os.listdir(template)) == 0:
            log(f"Sorry. Templates for {language} have not been implemented yet.")

        ## Move over all files to new directory
        log(f"Generating templates at {project_dir}")
        shutil.copytree(template, project_dir)

        ## Fill out project.yaml
        yaml_template = os.path.join(project_dir, "project.yaml")
        if not os.path.exists(yaml_template):
            log(f"Project yaml does not exist in {template}. Skipping.")
        file = Path(yaml_template)
        yaml = file.read_text()
        yaml = yaml.replace("{repo}", repo_url)
        yaml = yaml.replace("{email}", email)
        file.write_text(yaml)

        ## Fill out Dockerfile
        dockerfile_template = os.path.join(project_dir, "Dockerfile")
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
        build_template = os.path.join(project_dir, "build.sh")
        if not os.path.exists(build_template):
            log(f"build.sh does not exist in {template}. Skipping.")
        file = Path(build_template)
        build = file.read_text()
        build = build.replace("{year}", current_year)
        file.write_text(build)
            
        log("Project Config Generated. Warning: Some Config files may require further editing to be functional. This is especially true for " + 
            "projects that have many dependency requirements. From our testing, LLMs seem to be unreliable at this job.")
        
        log("WARNING: Make sure that you update the harness (indicated by fuzz_test.\{ext\}) to be at least " +
            "a minimal fuzz harness - the Fuzz Introspector cannot do its job without it, meaning no " +
            "functions can be selected for harness generation.")
    