import os

BASE_DIR = os.path.dirname(__file__)
OSS_FUZZ_DIR = os.path.join(BASE_DIR, "..", "oss-fuzz")

target_dir =  os.path.join(OSS_FUZZ_DIR, "projects")
output_dir = os.path.join(BASE_DIR, "script_output")
if not os.path.exists(output_dir):
    os.makedirs(output_dir)
output_file = os.path.join(output_dir, "project_repositories.txt")

with open(output_file, "w") as f_out:
    for project in sorted(os.listdir(target_dir)): 
        project_path = os.path.join(target_dir, project)
        if os.path.isdir(project_path):
            project_yaml = os.path.join(project_path, "project.yaml")
            if os.path.exists(project_yaml):
                with open(project_yaml, "r") as f:
                    yaml_content = f.read().splitlines()
                    for line in yaml_content:
                        if line.startswith("main_repo:"):
                            repository = line.split(":", 1)[1].strip().replace('"', '').replace("'", "")
                            f_out.write(f"{project}: {repository}\n")
            else:
                print(f"Warning: {project_yaml} does not exist.")
        else:
            print(f"Warning: {project_path} is not a directory.")
