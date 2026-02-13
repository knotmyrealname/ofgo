import os

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
SKIP_MODEL_CHECK = (os.environ['SKIP_MODEL_CHECK'] != 0) if 'SKIP_MODEL_CHECK' in os.environ else False

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