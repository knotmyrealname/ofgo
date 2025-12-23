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
import argparse

import harness_gen
import oss_fuzz_hook
from project_template_gen import generate_from_templates
from project_basis_gen import generate_project_basis
from logger_config import setup_logger
from helpers import *

DEFAULT_BUILD = 'template'

logger = setup_logger(color_text(__name__, ANSI_GREEN))
def log(msg):
    logger.info(msg)
def err(msg):
    logger.error(color_text(msg, ANSI_RED))
    sys.exit(1)
def warn(msg):
    logger.warning(color_text(msg, ANSI_YELLOW))

def run_interactive() -> None:
    """Runs OFGO in interactive mode, prompting user for all necessary inputs.
    
    Interactively guides the user through the process of onboarding a project,
    asking for a repository URL, build approach, language, email, model, and
    temperature settings.

    Raises:
        SystemExit: If certain input validation loops fail.
    """
    log("Running OFGO in interactive mode")
    try:
        email = None
        language = None
        build = None
        repo = input("Enter project repo URL or name: ").strip()
        if '.' in repo: ## Assumes url if there's a period - no current oss-fuzz projects have a period
            repo = sanitize_repo(repo)
            project = validate_repo_url(repo)

            build = input(f"Enter build approach: agent/template (default: {DEFAULT_BUILD}): ").strip()

            language = input("Enter project language: ").strip()
            check_language_support(language)
                
            while email is None:
                try:
                    email = input("Enter project maintainer email: ").strip()
                    check_email(email)
                except ValueError as ve:
                    email = None
                    log(f"Error: {ve}. Please reenter your email address.")
        else: 
            if project_exists(repo):
                project = repo
            else:
                raise ValueError(f"Project does not exist with name '{repo}'. If you're trying to generate a project, provide an URL instead.")
        model = input(f"Enter OpenAI model name (default: {DEFAULT_MODEL}): ").strip()
        if model == '':
            model = DEFAULT_MODEL
        temp = input(f"Enter OpenAI model temperature (default: {DEFAULT_TEMPERATURE}): ").strip()
        if temp == '':
            temperature = DEFAULT_TEMPERATURE
        else:
            temperature = int(temp)
        args = argparse.Namespace(repo=repo, project=project, email=email, model=model, language=language, temperature=temperature, build=build)
        run_full_suite(args)
    except ValueError as ve:
        err(ve)

def run_noninteractive(args: argparse.Namespace) -> None:
    """Runs OFGO with command-line arguments (non-interactive mode).
    
    Processes the provided arguments to validate the project and execute
    the full onboarding suite.

    Args:
        args: Parsed command-line arguments containing the repo, project, email,
            language, model, temperature, and build settings.

    Raises:
        SystemExit: If any validation fails.
    """
    log("Running OFGO fully")
    try:
        if '.' in args.repo:
            args.repo = sanitize_repo(args.repo)
            args.project = validate_repo_url(args.repo)
            check_language_support(args.language)
            check_email(args.email)
        else:
            if project_exists(args.repo):
                args.project = args.repo
            else:
                raise ValueError(f"Project does not exist with name '{args.repo}'. If you're trying to generate a project, provide an URL instead.")

        run_full_suite(args)
    except ValueError as ve:
        err(ve)

def run_full_suite(args: argparse.Namespace) -> None:
    """Runs the complete OFGO onboarding suite.
    
    Executes the project basis generation, template generation, harness
    generation, and compilation checks as needed based on the arguments.

    Args:
        args: Parsed command-line arguments with project configuration.
    """
    if '.' in args.repo:
        if args.build == 'agent':
            log("agent mode was chosen for build files")
            run_basis_gen(args)
        else:
            log("template mode was chosen for build files (default)")
            run_template_gen(args)
    else:
        log("No build necessary.")
        check_project_compilation(args.project)
    run_harnessgen(args)
    ## No need to run OSS-Fuzz directly as harness_gen already outputs coverage results

def run_basis_gen(args: argparse.Namespace) -> None:
    """Generates project structure using an agent-based approach.
    
    Validates the model and temperature, then runs the project basis
    generation to create project.yaml, build.sh, and Dockerfile.

    Args:
        args: Command-line arguments containing the repo, email, and model.

    Raises:
        SystemExit: If model validation fails.
    """
    try:
        print(SKIP_MODEL_CHECK)
        validate_model(args.model, args.temperature)
    except ValueError as ve:
        err(ve)
    log(f"Generating project structure with {args.repo}, {args.email}")
    repo_dir = generate_project_basis(args.repo, args.email, args.model)

def run_template_gen(args: argparse.Namespace) -> None:
    """Generates project structure using static templates.
    
    Creates project.yaml, build.sh, and Dockerfile from templates
    for the specified language.

    Args:
        args: Command-line arguments containing the repo, email, language, and model.
    """
    log(f"Generating project with a template")
    generate_from_templates(args.repo, args.email, args.language, args.model)

def run_harnessgen(args: argparse.Namespace) -> None:
    """Generates harnesses for a project and consolidates them.
    
    Validates the model and temperature, then generates fuzz harnesses
    and consolidates them into a single directory.

    Args:
        args: Command-line arguments containing project, model, and temperature.

    Raises:
        SystemExit: If model validation fails.
    """
    try:
        validate_model(args.model, args.temperature)
    except ValueError as ve:
        err(ve)
    log(f"Generating harness for {args.project}")
    harness_gen.generate_harness(args.model, args.project, args.temperature)
    harness_gen.consolidate_harnesses(args.project)

def run_ossfuzz(args: argparse.Namespace) -> None:
    """Runs OSS-Fuzz on a project with its harnesses.
    
    Executes the OSS-Fuzz fuzzing pipeline on the specified project.

    Args:
        args: Command-line arguments containing the project name.

    Raises:
        SystemExit: If the project does not exist in OSS-Fuzz.
    """
    if not os.path.exists(os.path.join(OSS_FUZZ_DIR, f"projects/{args.project}")):
        raise ValueError(f"Project '{args.project}' does not exist in OSS-Fuzz")
    log(f"Running OSS-Fuzz on {args.project}")
    oss_fuzz_hook.run_project(args.project)

def run_corpusgen(args: argparse.Namespace) -> None:
    """Generates input corpus for a project (not yet implemented).
    
    Placeholder function for corpus generation functionality.

    Args:
        args: Command-line arguments containing the project name.

    Note:
        This feature is not yet implemented.
    """
    ##TODO
    warn("Corpus Generation not yet Implemented")

def run_on_args() -> None:
    """Parses and executes OFGO commands from command-line arguments.
    
    Sets up the argument parser with all available subcommands and executes
    the appropriate function based on user input.

    Raises:
        SystemExit: If no command is provided or execution fails.
    """
    parser = argparse.ArgumentParser(
        prog="ofgo",
        description="Onboard project into OSS-Fuzz-Gen",
        add_help=False
    )

    # Global -h/--help flag
    parser.add_argument('-h', '--help', action='store_true', help="Show this help message and exit")

    subparsers = parser.add_subparsers(dest='command', help="Available commands")

    # Run the full pipeline
    ni = subparsers.add_parser('default', help="Full onboarding with harness and corpii generation (future feature)")
    ni.add_argument('--repo', type=str, help="Project repo URL")
    ni.add_argument('--email', type=str, help="Project maintainer email")
    ni.add_argument('--model', type=str, default=DEFAULT_MODEL, help="OpenAI model name")
    ni.add_argument('--build', type=str, default=DEFAULT_BUILD, help="'agent' for experimental AI Agent build approach. Omit for simple Template approach")
    ni.add_argument('--temperature', type=int, default=DEFAULT_TEMPERATURE, help="Temperature for OpenAI model")
    ni.add_argument('--language', type=str, help="Programming language of project to fuzz")
    ni.set_defaults(func=run_noninteractive)

    # Run only basis gen
    ba = subparsers.add_parser('basis', help="Generate skeleton of the harness (project.yaml, build.sh, Dockerfile, empty-fuzzers) using OSS-Fuzz-Gen Build_Generator Agent Mode")
    ba.add_argument('--repo', type=str, help="Project repo URL")
    ba.add_argument('--email', type=str, help="Project maintainer email")
    ba.add_argument('--model', type=str, default=DEFAULT_MODEL, help="OpenAI model name")
    ba.set_defaults(func=run_basis_gen)

    # Run only template gen
    te = subparsers.add_parser('template', help="Uses static templates to generate skeleton of the harness (project.yaml, build.sh, Dockerfile, empty-fuzzer)")
    te.add_argument('--repo', type=str, help="Project repo URL")
    te.add_argument('--email', type=str, help="Project maintainer email")
    te.add_argument('--language', type=str, help="Programming language of project to fuzz")
    te.add_argument('--model', type=str, default=DEFAULT_MODEL, help="OpenAI model name")
    te.set_defaults(func=run_template_gen)

    # Run only OSS-Fuzz-gen
    pe = subparsers.add_parser('existing', help="Run OSS-Fuzz-Gen on an existing project")
    pe.add_argument('--project', type=str, help="Project name")
    pe.add_argument('--model', type=str, default=DEFAULT_MODEL, help="OpenAI model name")
    pe.add_argument('--temperature', type=int, default=DEFAULT_TEMPERATURE, help="Temperature for OpenAI model")
    pe.set_defaults(func=run_harnessgen)

    # Run OSS-Fuzz
    cv = subparsers.add_parser('coverage', help="Get coverage reports for project")
    cv.add_argument('--project', type=str, help="Project name")
    cv.set_defaults(func=run_ossfuzz)

    # Run corpus generation
    cg = subparsers.add_parser('corpus-gen', help="Generate corpora for a project")
    cg.add_argument('--project', type=str, help="Project name")
    cg.add_argument('--model', type=str, default=DEFAULT_MODEL, help="OpenAI model name")
    cg.add_argument('--temperature', type=int, default=DEFAULT_TEMPERATURE, help="Temperature for OpenAI model")
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
        err("No command provided. Use --help or -h for usage details.")
    args.func(args)

def main() -> None:
    """Main entry point for the OFGO application.
    
    Determines whether to run in interactive or command-line mode based on
    the presence of arguments, then executes the appropriate mode.
    """
    if len(sys.argv) == 1:
        run_interactive()
    else :
        run_on_args()

if __name__ == '__main__':
    main()
