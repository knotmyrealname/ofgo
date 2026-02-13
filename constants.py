import os

######################################################
## File/Directory Locations
######################################################
BASE_DIR = os.path.dirname(__file__)
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
OSS_FUZZ_DIR = os.path.join(BASE_DIR, "oss-fuzz")
OSS_FUZZ_PROJECTS_DIR = os.path.join(OSS_FUZZ_DIR, "projects")
INFRA_HELPER = os.path.join(OSS_FUZZ_DIR, "infra", "helper.py")
OSS_FUZZ_GEN_DIR = os.path.join(BASE_DIR, "oss-fuzz-gen")
INTROSPECTOR_DIR = os.path.join(BASE_DIR, "fuzz-introspector")
PERSISTENCE_DIR = os.path.join(BASE_DIR, "gen-projects")
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")
WORK_DIR = os.path.join(BASE_DIR, "work")
GIT_REPO_DIR = os.path.join(WORK_DIR, "ofgo", "repositories")
RESULTS_DIR = os.path.join(BASE_DIR, "results")
REPORT_DIR = os.path.join(BASE_DIR, "report")
GENERATED_SAMPLES_DIR = os.path.join(PERSISTENCE_DIR, "SAMPLES")

######################################################
## Execution Parameters
######################################################
DEFAULT_MODEL = 'gpt-4o-mini'
DEFAULT_TEMPERATURE = 0.4
BENCHMARK_HEURISTICS = "far-reach-low-coverage,low-cov-with-fuzz-keyword,easy-params-far-reach"
NUMBER_OF_HARNESSES = 2 # How many fuzzing harnesses to generate
NUM_SAMPLES = 1 # Currently only supports 1 - may lead to unexpected behavior if it's increased
DEFAULT_BUILD = 'template'

######################################################
## Environmental Variables
######################################################
OPENAI_API_KEY = os.environ['OPENAI_API_KEY'] if 'OPENAI_API_KEY' in os.environ else None
INTROSPECTOR_PORT = os.environ['WEBAPP_PORT'] if 'WEBAPP_PORT' in os.environ else '8080'
SKIP_MODEL_CHECK = (os.environ['SKIP_MODEL_CHECK'] != 0) if 'SKIP_MODEL_CHECK' in os.environ else False

######################################################
## Dict of supported languages and their file extensions
######################################################
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

######################################################
## ANSI Color Codes
######################################################
ANSI_BLACK = 90
ANSI_RED = 91
ANSI_GREEN = 92
ANSI_YELLOW = 93
ANSI_LIGHT_PURPLE = 94
ANSI_PURPLE = 95
ANSI_CYAN = 96
ANSI_GRAY = 97