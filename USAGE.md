# In order to populate the submodules run the following:
```
git submodule set-url -- oss-fuzz-gen \
https://github.com/knotmyrealname/oss-fuzz-gen

git submodule set-url -- oss-fuzz \
https://github.com/google/oss-fuzz.git

git submodule update --init --recursive
```

# Follow the steps in the [README](./README.md) to setup the python environment to run this tool

## Logging
All operations are logged with colored output to the console.

# Setting the environment variable for open-ai api key
```export OPENAI_API_KEY="your-api-key-here"``` 

# For harness generation of projects that need complete setup (build.sh, project.yaml, and Dockerfile)
```
python3 ofgo.py default \
  --repo <REPO_URL> \
  --email <MAINTAINER_EMAIL> \
  [--model gpt-5] \
  [--temperature 1] 
  ``` 

# To create new harnesses for existing projects
```
python3 ofgo.py pre-existing \
  --project <PROJECT_NAME> \
  [--model gpt-5] \
  [--temperature 1]
```

# Only generating coverage reports for existing projects
```
python3 ofgo.py coverage \
  --project <PROJECT_NAME>
```

# Creating new seed corpuses using LLMs
```
python3 ofgo.py corpus-gen \
  --project <PROJECT_NAME> \
  [--model gpt-5] \
  [--temperature 1]
```

# Only generating configuration files (Dockerfile, build.sh, project.yaml) for a new project (no harnesses)
```
python3 project_basis_gen.py <REPOSITORY_URL> <MAINTAINER_EMAIL>
```
- To specify a preferred model (defaults to gpt-4) or work directory (defaults to current directory)
```python
python3 project_basis_gen.py <REPOSITORY_URL> <MAINTAINER_EMAIL> --work <PATH_TO_WORK_DIR> --model <MODEL_NAME> 
```
