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

import shlex
import sys
import os
import re
import argparse
import logging
from email_validator import validate_email, EmailNotValidError
from urllib.parse import urlparse
import openai

import harness_gen
import oss_fuzz_hook
from project_basis_gen import generate_project_basis
from logger_config import setup_logger

BASE_DIR = os.path.dirname(__file__)
DEFAULT_MODEL = "gpt-4o-mini"

## System-wide params
OSS_FUZZ_DIR = os.path.join(BASE_DIR, "oss-fuzz")
OSS_FUZZ_GEN_DIR = os.path.join(BASE_DIR, "oss-fuzz-gen")

logger = setup_logger(__name__)

def log(output): ## Green rep
    logger.info(f"\033[92moss_fuzz_gen_onboarding:\033[00m {output}")

def check_email(email):
    regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    if not bool(re.fullmatch(regex, email)):
        raise ValueError(f'Invalid email. Please reenter your email address')
    try:
        valid_email = validate_email(email)
        return valid_email.email
    except EmailNotValidError as e:
        raise ValueError(f'Invalid email. Please reenter your email address') from e

def sanitize_repo(url) :
    regex = re.compile(r'https?://[^\s/$.?#].[^\s]*')
    if not bool(regex.fullmatch(url)):
        raise ValueError(f'Cannot access repository at {url}. Make sure your project is publicly accessible and that there are no problems with the link.')
    parsed = urlparse(url)
    if not parsed.netloc.endswith('github.com') and not parsed.netloc.endswith('gitlab.com'):
        raise ValueError(f'URL {url} not GitHub or GitLab')
    if parsed.scheme != 'https':
        raise ValueError(f'URL {url} not HTTPS')
    return shlex.quote(url)

def run_interactive():
    log('Running OFGO in interactive mode')
    try:
        project = None
        choice = input('Is the project already in OSS-Fuzz? (y/n): ').strip().lower()
        if choice == 'y':
            project = input('Enter project name in OSS-Fuzz: ').strip()
        repo = input('Enter project repo URL: ').strip()
        email = input('Enter project maintainer email: ').strip()
        check_email(email)
        repo = sanitize_repo(repo)
        model = input(f'Enter OpenAI model name (default: {DEFAULT_MODEL}): ').strip()
        if model == '':
            model = DEFAULT_MODEL
        temp = input('Enter OpenAI model temperature (default: 1): ').strip()
        if temp == '':
            temperature = 1
        else:
            temperature = int(temp)
        args = argparse.Namespace(repo=repo, email=email, model=model, temperature=temperature)
        run_basis_gen(args)
        run_harnessgen(args)
        if project and project != '':
            run_ossfuzz(args)
    except ValueError as ve:
        print(f'Error: {ve}')
        sys.exit(1)

def run_noninteractive(args):
    log('Running OFGO fully')
    try:
        check_email(args.email)
        args.repo = sanitize_repo(args.repo)
        run_basis_gen(args)
        run_harnessgen(args)
        if args.project:
            run_ossfuzz(args)
    except ValueError as ve:
        print(f'Error: {ve}')
        sys.exit(1)

def run_basis_gen(args):
    log(f'Generating project structure with {args.repo}, {args.email}')
    repo_dir = generate_project_basis(args.repo, args.email)

def run_harnessgen(args):
    validate_model(args.model, args.temperature)
    if not project_exists(args.project):
        raise ValueError(f'Project {args.project} does not exist in OSS-Fuzz')
    log(f'Generating harness for {args.project}')
    harness_gen.generate_harness(args.model, args.project, args.temperature)

def run_ossfuzz(args):
    if not project_exists(args.project):
        raise ValueError(f'Project {args.project} does not exist in OSS-Fuzz')
    log(f'Running OSS-Fuzz on {args.project}')
    oss_fuzz_hook.run_project(args.project)

def run_corpusgen(args):
    ##TODO
    print(f"corpusgen {project}")

def project_exists(project):
    project_location = os.path.join(BASE_DIR, f"oss-fuzz/projects/{project}")
    return os.path.exists(project_location)

## Note that this will use a small amount of API credits if successful
def validate_model(model, temperature):
    ## Get API key
    try:
        client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    except:
        log('''Program execution failed: Missing OpenAI API Key.
Make sure to export your API Key via the following command:
   export OPENAI_API_KEY={your_api_key}''')
        sys.exit(1)
        
    ## Check model
    try:
        response = client.responses.create(model=model, 
                                           input="test", 
                                           max_output_tokens=16,
                                           temperature=temperature)
    except Exception as e:
        log(f'''Failed to generate test response. OpenAI API response:
{e}''')
    return 

def run_on_args():
    parser = argparse.ArgumentParser(
        prog='ofgo',
        description='Onboard project into OSS-Fuzz-Gen',
        add_help=False
    )

    # Global -h/--help flag
    parser.add_argument('-h', '--help', action='store_true', help='Show this help message and exit')

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Run the default
    ni = subparsers.add_parser('default', help='Full onboarding with harness and corpii generation')
    ni.add_argument('--repo', type=str, help='Project repo URL')
    ni.add_argument('--email', type=str, help='Project maintainer email')
    ni.add_argument('--model', type=str, default=DEFAULT_MODEL, help='OpenAI model name')
    ni.add_argument('--temperature', type=int, default=1, help='Temperature for OpenAI model')
    ni.set_defaults(func=run_noninteractive)

    # Run only OSS-Fuzz-gen
    pe = subparsers.add_parser('pre-existing', help='Run OSS-Fuzz-Gen on pre-existing project')
    pe.add_argument('--project', type=str, default='all', help='Project name')
    pe.add_argument('--model', type=str, default=DEFAULT_MODEL, help='OpenAI model name')
    pe.add_argument('--temperature', type=int, default=1, help='Temperature for OpenAI model')
    pe.set_defaults(func=run_harnessgen)

    # Run OSS-Fuzz
    cv = subparsers.add_parser('coverage', help='Get coverage reports for project')
    cv.add_argument('--project', type=str, default='all', help='Project name')
    cv.set_defaults(func=run_ossfuzz)

    # Run corpus generation
    cg = subparsers.add_parser('corpus-gen', help='Generate corpora for a project')
    cg.add_argument('--project', type=str, default='all', help='Project name')
    cg.add_argument('--model', type=str, default=DEFAULT_MODEL, help='OpenAI model name')
    cg.add_argument('--temperature', type=int, default=1, help='Temperature for OpenAI model')
    cg.set_defaults(func=run_corpusgen)

    # Handle command arguments
    arguments = sys.argv[1:]

    # Handle --help and -h
    if '-h' in arguments or '--help' in arguments:
        parser.print_help()
        sys.exit(0)
    
    # Handle all options
    args = parser.parse_args(arguments)
    if args.command is None:
        print("Error: No command provided. Use --help or -h for usage details.")
        sys.exit(1)
    args.func(args)

def main():
    if len(sys.argv) == 1:
        run_interactive()
    else :
        run_on_args()

if __name__ == "__main__":
    main()