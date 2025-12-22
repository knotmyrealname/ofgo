import os
import re
import shutil
import sys
import git
import openai
import shlex
import subprocess

from urllib.parse import urlparse
from email_validator import validate_email, EmailNotValidError

from logger_config import setup_logger

BASE_DIR = os.path.dirname(__file__)
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
OSS_FUZZ_DIR = os.path.join(BASE_DIR, "oss-fuzz")
OSS_FUZZ_PROJECTS_DIR = os.path.join(OSS_FUZZ_DIR, "projects")
OSS_FUZZ_GEN_DIR = os.path.join(BASE_DIR, "oss-fuzz-gen")
INTROSPECTOR_DIR = os.path.join(BASE_DIR, "fuzz-introspector")
INFRA_HELPER = os.path.join(OSS_FUZZ_DIR, "infra", "helper.py")
PERSISTENCE_DIR = os.path.join(BASE_DIR, "gen-projects")
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")
WORK_DIR = os.path.join(BASE_DIR, "work")
GIT_REPO_DIR = os.path.join(WORK_DIR, "ofgo", "repositories")

DEFAULT_MODEL = 'gpt-4o-mini'
DEFAULT_TEMPERATURE = 0.4
## Turns off and on the OPENAI_API Key checks - Defaults to true
SKIP_MODEL_CHECK = True if 'SKIP_MODEL_CHECK' in os.environ else False

## Dict of supported languages and their file extensions
LANGUAGE_EXTS = {
    'c': 'c',
    'c++': 'cpp',
    'go': 'go',
    'javascript': 'js',
    'jvm': 'java',
    'python': 'py',
    'ruby': 'rb',
    'rust': 'rs',
    'swift': 'swift'
}

ANSI_BLACK = 90
ANSI_RED = 91
ANSI_GREEN = 92
ANSI_YELLOW = 93
ANSI_LIGHT_PURPLE = 94
ANSI_PURPLE = 95
ANSI_CYAN = 96
ANSI_GRAY = 97

def color_text(text: str, color: str):
    return f"\033[{color}m{text}\033[00m"

helper_logger = setup_logger(color_text(__name__, ANSI_GREEN))
def helper_log(msg):
    helper_logger.info(msg)
def helper_err(msg):
    helper_logger.error(color_text(msg, ANSI_RED))
    sys.exit(1)

def check_language_support(language: str):
    if language in LANGUAGE_EXTS:
        return
    elif language is None or language == '':
        raise ValueError("Unable to identify language.")
    else:
        raise ValueError(f"Language not supported: {language}.")

def ensure_dir_exists(path: str):
    if not os.path.exists(path):
        os.makedirs(path)

def sync_dirs(src_dir, dest_dir):
    '''
    Syncs two directories by deleting dest_dir (if it exists) and copying over src_dir
    '''
    if os.path.exists(dest_dir):
        shutil.rmtree(dest_dir)
    shutil.copytree(src_dir, dest_dir)

def clean_dir(path: str):
    '''Delete a directory/symlink if it exists.'''
    if os.path.islink(path):
        os.unlink(path)
    elif os.path.isdir(path):
        shutil.rmtree(path)
    elif os.path.exists(path):
        os.unlink(path)
    
def project_exists(project: str):
    persistent_project = os.path.join(PERSISTENCE_DIR, project)
    oss_fuzz_project = os.path.join(OSS_FUZZ_PROJECTS_DIR, project)
    if os.path.isdir(persistent_project) or os.path.isdir(oss_fuzz_project):
        return True
    return False

def check_email(email):
    regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    if not bool(re.fullmatch(regex, email)):
        raise ValueError(f"Invalid email")
    try:
        valid_email = validate_email(email)
        return valid_email.email
    except EmailNotValidError as e:
        raise ValueError(f"Invalid email") from e

def validate_repo_url(url: str) -> str:
    ## Check to make sure repo is valid
    project_name = sanitize_repo_name(url)
    try:
        project_repo_dir = os.path.join(GIT_REPO_DIR, project_name)
        if os.path.exists(project_repo_dir):
            shutil.rmtree(project_repo_dir)
        git.Repo.clone_from(url, project_repo_dir, filter=["blob:none"])
        return project_name
    except git.exc.GitError as e:
        raise ValueError(f"ERROR! Couldn't pull from {url}: \n{e}")

def sanitize_repo(url):
    regex = re.compile(r'https?://[^\s/$.?#].[^\s]*')
    if not bool(regex.fullmatch(url)):
        raise ValueError(f"Not a valid URL")
    parsed = urlparse(url)
    if not parsed.netloc.endswith('github.com') and not parsed.netloc.endswith('gitlab.com'):
        raise ValueError(f"URL {url} not GitHub or GitLab")
    if parsed.scheme != 'https':
        raise ValueError(f"URL {url} not HTTPS")
    return shlex.quote(url)

def sanitize_repo_name(repo_url: str) -> str:
    '''Extracts an OSS-Fuzz project name (lowercase repo name).'''
    name = os.path.basename(repo_url).replace('.git', '').strip().lower()
    if not name:
        raise ValueError(f"Could not parse repository name from URL: {repo_url}")
    return name

## Note that this will use a small amount of API credits if successful
def validate_model(model, temperature):
    global SKIP_MODEL_CHECK
    if SKIP_MODEL_CHECK: return
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
    SKIP_MODEL_CHECK = True
    return 

def check_project_compilation(project_name: str):
    persistent_project_dir = os.path.join(PERSISTENCE_DIR, project_name)
    project_dir = os.path.join(OSS_FUZZ_DIR, "projects", project_name)
    
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