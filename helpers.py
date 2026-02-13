import os
import re
import shutil
import sys
import git
import openai
import subprocess

from urllib.parse import urlparse
from email_validator import validate_email, EmailNotValidError

from logger_config import setup_logger
from constants import *

def color_text(text: str, color: str):
    return f"\033[{color}m{text}\033[00m"

helper_logger = setup_logger(color_text(__name__, ANSI_GREEN))
def helper_log(msg):
    helper_logger.info(msg)
def helper_err(msg):
    helper_logger.error(color_text(msg, ANSI_RED))
    sys.exit(1)

def check_language_support(language: str) -> None:
    """Verifies that a programming language is supported.

    Args:
        language (str): The programming language to check.

    Raises:
        ValueError: If the language is None, empty, or not supported.
    """
    if language in LANGUAGE_EXTS:
        return
    elif language is None or language == '':
        raise ValueError("Unable to identify language.")
    else:
        raise ValueError(f"Language not supported: {language}.")

def ensure_dir_exists(path: str) -> None:
    """Creates a directory if it does not already exist.

    Args:
        path (str): The directory path to create.
    """
    if not os.path.exists(path):
        os.makedirs(path)

def sync_dirs(src_dir: str, dest_dir: str) -> None:
    """Syncs two directories by replacing the destination with the source.
    Not super efficient, but it's more reliable than symlinks and is fine at
    our file sizes.
    
    Deletes the destination directory (if it exists) and copies the source
    directory to the destination location.

    Args:
        src_dir (str): The source directory path to copy from.
        dest_dir (str): The destination directory path to replace.
    """
    if os.path.exists(dest_dir):
        shutil.rmtree(dest_dir)
    shutil.copytree(src_dir, dest_dir)

def clean_dir(path: str) -> None:
    """Deletes a directory, symlink, or file if it exists. If a failure is discovered
    (likely due to write-only files) a fallback mode is activated to delete the files
    that can be deleted

    Args:
        path (str): The path to the directory, symlink, or file to delete.
    """
    if os.path.islink(path): 
        ## Is symlink - assuming never write protected
        os.unlink(path)
    elif os.path.isdir(path): 
        ## Is directory - may be write-protected
        try:
            shutil.rmtree(path)
        except:
            ## More inefficient fallback to remove the files that can be removed
            for root, dir, files in os.walk(path):
                for file in files:
                    try:
                        os.remove(path)
                    except:
                        None
    elif os.path.exists(path):
        ## Should be a file - may be write-protected
        try:
            os.remove(path)
        except:
            return
    
def project_exists(project: str) -> bool:
    """Checks if a project exists in either the persistence or OSS-Fuzz directory.

    Args:
        project (str): The project name to check for.

    Returns:
        bool: True if the project exists in either location, False otherwise.
    """
    persistent_project = os.path.join(PERSISTENCE_DIR, project)
    oss_fuzz_project = os.path.join(OSS_FUZZ_PROJECTS_DIR, project)
    if os.path.isdir(persistent_project) or os.path.isdir(oss_fuzz_project):
        return True
    return False

def check_email(email: str) -> str:
    """Validates and returns an email address.

    Args:
        email (str): The email address to validate.

    Returns:
        str: A safe and validated version of the email address.

    Raises:
        ValueError: If the email format is invalid.
    """
    regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    if not bool(re.fullmatch(regex, email)):
        raise ValueError(f"Invalid email")
    try:
        valid_email = validate_email(email)
        return valid_email.email
    except EmailNotValidError as e:
        raise ValueError(f"Invalid email") from e

def validate_repo_url(url: str) -> str:
    """Validates and clones a repository from a given URL.
    
    Checks that the URL is valid, then clones it to a temporary directory
    to verify it's accessible.

    Args:
        url (str): The repository URL to validate.

    Returns:
        str: The sanitized project name extracted from the repository.

    Raises:
        ValueError: If the URL is invalid or cannot be cloned.
    """
    ## Check to make sure repo is valid and safe before attempting to download
    project_name = sanitize_repo_name(url)
    try:
        project_repo_dir = os.path.join(GIT_REPO_DIR, project_name)
        if os.path.exists(project_repo_dir):
            shutil.rmtree(project_repo_dir)
        git.Repo.clone_from(url, project_repo_dir, filter=["blob:none"])
        return project_name
    except git.exc.GitError as e:
        raise ValueError(f"ERROR! Couldn't pull from {url}: \n{e}")

def sanitize_repo_name(repo_url: str) -> str:
    """Extracts an OSS-Fuzz project name from a repository URL.
    
    Converts the repository name to lowercase and removes .git suffix.

    Args:
        repo_url (str): The repository URL to extract the project name from.

    Returns:
        str: The sanitized project name in lowercase.

    Raises:
        ValueError: If the project name cannot be parsed from the URL.
    """
    name = os.path.basename(repo_url).replace('.git', '').replace('.','-').strip().lower()
    if not name:
        raise ValueError(f"Could not parse repository name from URL: {repo_url}")
    return name

## Note that this will use a small amount of API credits if successful
def validate_model(model: str, temperature: float) -> None:
    """Validates that a model and cooresponding temperature settings are valid.
    
    Currently only supports OpenAI models - Sends a test request to the OpenAI API 
    to verify the model is accessible and the temperature is valid. This can be
    turned off by modifying SKIP_MODEL_CHECK to be True.

    Args:
        model (str): The model name to validate.
        temperature (float): The temperature setting to validate.

    Raises:
        ValueError: If the API key is missing, invalid, or the model fails to respond.
    """
    global SKIP_MODEL_CHECK
    if SKIP_MODEL_CHECK: 
        helper_log(SKIP_MODEL_CHECK)
        helper_log("Skipping Model Check")
        return
    ## Get API key
    try:
        client = openai.OpenAI(api_key=os.environ['OPENAI_API_KEY'])
    except:
        raise ValueError("""Program execution failed: Missing OpenAI API Key.
Make sure to export your API Key via the following command:
   export OPENAI_API_KEY={your_api_key}""")
        
    ## Check model
    try:
        response = client.responses.create(model=model, 
                                           input="test", 
                                           max_output_tokens=16,
                                           temperature=temperature)
    except Exception as e:
        raise ValueError(f"""Failed to generate test response. OpenAI API response:
{e}""")
    ## We only need to check the model params once
    SKIP_MODEL_CHECK = True
    return 

def check_project_compilation(project_name: str):
    persistent_project_dir = os.path.join(PERSISTENCE_DIR, project_name)
    project_dir = os.path.join(OSS_FUZZ_DIR, "projects", project_name)
    
    if os.path.exists(persistent_project_dir):
        sync_dirs(persistent_project_dir, project_dir)
    clean_dir(os.path.join(OSS_FUZZ_DIR, "build", "out"))

    ## Test project on OSS-Fuzz and make sure it compiles and runs without errors
    helper_log(f"Testing with OSS-Fuzz to ensure compilation:")

    ## Ensure all three are the same length - length is based off of commands
    commands = [
        ["python3", INFRA_HELPER, "pull_images"],
        ["python3", INFRA_HELPER, "build_image", project_name, "--pull"],
        ["python3", INFRA_HELPER, "build_fuzzers", project_name]
    ]
    success_res = [
        "Successfully pulled OSS-Fuzz images.",
        f"Successfully built images for {project_name}.",
        f"Successfully built fuzzers for {project_name}."
    ]
    error_res = [
        "Failed to pull OSS-Fuzz images.",
        f"Failed to build images for {project_name}: stderr output is printed above.",
        f"Failed to build fuzzers for {project_name}: stderr output is printed above."
    ]
    helper_log("Note: The first image pull of the day may take a while.")
    for i in range(len(commands)):
        helper_log(f"Running: {' '.join(commands[i])}")
        res = subprocess.run(commands[i], capture_output=True)
        if res.returncode != 0:
            helper_log(f"\n{res.stderr.decode()}")
            helper_err(error_res[i])
        else:
            helper_log(success_res[i])

    fuzz_dir = os.path.join(os.path.join(OSS_FUZZ_DIR, "build", "out", project_name))
    if not os.path.exists(fuzz_dir):
        helper_err(f"Could not locate fuzzing harnesses at {fuzz_dir}")
    
    fuzzers = []
    for root, dirs, files in os.walk(fuzz_dir):
        for file in files:
            if (file.startswith("fuzz_") or file.endswith("Fuzzer") or re.match(r'^fuzz-harness-\d+_\d+\$', file)) and '.' not in file:
                fuzzers.append(file)
    if not fuzzers:
        helper_err(f"Unable to locate any fuzzing harnesses in {fuzz_dir}")
    for fuzzer in fuzzers:
        command = ["python3", INFRA_HELPER, "run_fuzzer", project_name, fuzzer, "--", "-max_total_time=5", "-runs=10"]
        helper_log(f"Running: {' '.join(command)}")
        res = subprocess.run(command, capture_output=True)
        if res.returncode != 0:
            helper_log(f"\n{res.stderr.decode()}")
            helper_err(f"Failed to run {fuzzer}.")
        else:
            helper_log(f"Successfully ran {fuzzer}.")
    helper_log(f"All fuzzers ran successfully.")