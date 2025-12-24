import os
import sys

## Note: This is not optimized - we are not working with large enough folders so a simple n^2 search is fine

BASE_DIR = os.path.dirname(__file__)
OSS_FUZZ_DIR = os.path.join(BASE_DIR, "..", "oss-fuzz")

target_dir =  os.path.join(OSS_FUZZ_DIR, "projects")
temp_dir =  os.path.join(OSS_FUZZ_DIR, "temp_projects")
source_file =  os.path.join(BASE_DIR, "script_output","projects_by_language","python_projects.txt")

if len(sys.argv) == 2: 
    ## Moves all of the directories in temp_projects back to projects given the reset argument
    if sys.argv[1] == 'reset':
        if os.path.exists(temp_dir):
            for project in os.listdir(temp_dir):
                project_path = os.path.join(temp_dir, project)
                os.rename(project_path, os.path.join(target_dir, project))
    else: ## assume a file if it's not 'reset'
        source_file = os.path.join(BASE_DIR, sys.argv[1])
elif len(sys.argv) > 2:
    print("Error: Too Many Args!")
else:
    # Uses the source file to move projects between the projects and temp projects dir
    with open(source_file, 'r') as f:
        desired_packages = f.read().splitlines()

    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    target_dir_projects = sorted(os.listdir(target_dir))
    temp_dir_projects = sorted(os.listdir(temp_dir))

    for project in target_dir_projects:
        if project not in desired_packages:
            project_path = os.path.join(target_dir, project)
            if os.path.isdir(project_path):
                os.rename(project_path, os.path.join(temp_dir, project))
            else:
                print(f"Error: {project_path} is not a directory.")
    for project in temp_dir_projects:
        if project in desired_packages:
            project_path = os.path.join(temp_dir, project)
            if os.path.isdir(project_path):
                os.rename(project_path, os.path.join(target_dir, project))
            else:
                print(f"Error: {project_path} is not a directory.")

