# Usage Guide for OFGO

## Before you start:
Make sure to follow the steps in the [README](./README.md) to setup your environment, if you haven't done so already. You will need to be within the `ofgo` directory, cloned during setup, to run these commands.

## Logging
All operations are logged with colored name output to the console, signifying the step of the out. Warning messages are fully colored in yellow and may allow further program execution while Error messages are fully colored in red and are proceeded by a system exit.

## Environmental Variables
OFGO recognizes the following environmental variables:
- `OPENAI_API_KEY=<your-api-key>` - The API key to access various OPEN-AI models. This is only necessary for LLM-related tasks - it is not checked for parts of the pipeline that do not require an LLM, such as template generation and OSS-Fuzz results
- `SKIP_MODEL_CHECK=<0/1>` - By setting this environmental variable, the model check can be bypassed, enabling testing or Google Vertex models to be ran - our functionality does not currently support checks for a valid Google Vertex model. To bypass the model check, set this variable to anything other than `0`, and set it to `0` or remove the variable to re-enable the check.
- `WEBAPP_PORT=<port>` - By default, port 8080 on `localhost` is used for the local Fuzz Introspector Webserver. If you want to update this for any reason, you can set this environmental variable.

There are also additional environmental variables that are supported by OSS-Fuzz-Gen. We believe the following may be important:

### OSS-Fuzz-Gen

**Vertex AI** (follow the [OSS-Fuzz-Gen guide](https://github.com/google/oss-fuzz-gen/blob/main/USAGE.md) for full setup as things may change). 

**Reminder:** Set the environmental variable `SKIP_MODEL_CHECK=1` if using Vertex AI.

- `CLOUD_ML_PROJECT_ID=<gcp-project-id>` - The project id associated with the Google Cloud project you want to use for Vertex AI. This project must have the Vertex AI API enabled to run OSS-Fuzz-Gen.
- `VERTEX_AI_LOCATIONS=us-west1,us-west4,us-east4,us-central1` - A list of the datacenters you want to run Vertex AI on. You must have Vertex AI quota on a specific datacenter to be able to utilize it.

**Azure OpenAI API key** We do not current support model checks for Azure OpenAI keys - skip the model check for Azure by setting `SKIP_MODEL_CHECK=1`. To run with OpenAI keys hosted on Azure, you'll need to export the following environmental variables and add `-azure` to the end of the OpenAI model (not all models may be supported):

- `AZURE_OPENAI_API_KEY=<your-azure-api-key>`
- `AZURE_OPENAI_ENDPOINT=<your-azure-endpoint>`
- `AZURE_OPENAI_API_VERSION=<your-azure-api-version>`

### Exporting Environmental variables
To export an environmental variable in linux, you simply have to run the command:

`export <ENVIRONMENTAL_VARIABLE=<VALUE>>`

e.g. `export SKIP_MODEL_CHECK=1`

You can chain these together before the execution of your program, with an example execution as follows:

```
export SKIP_MODEL_CHECK=1 && export WEBAPP_PORT=8081 && export CLOUD_ML_PROJECT_ID=ofgo-486423 && export VERTEX_AI_LOCATIONS=us-central1 && python ofgo.py <command1> <arg1> <command2> <arg2> ...
```

or export them before running ofgo:
```
export SKIP_MODEL_CHECK=1 && export WEBAPP_PORT=8081 && export CLOUD_ML_PROJECT_ID=ofgo-486423 && export VERTEX_AI_LOCATIONS=us-central1

python ofgo.py <command1> <arg1> <command2> <arg2> ...
```


# Running OFGO

## Project Generation
This pipeline facilitates the creation of new OSS-Fuzz projects. Before you begin, we recommend checking to make sure that your project fits within OSS-Fuzz's criteria (see our [OSS-Fuzz explainer](./README.md#what-is-oss-fuzz)). We currently offer both an interactive and single-command execution option as well as a choice between trying the experimental OSS-Fuzz-gen project generation or working with a template.

### Interactive Generation
To run via our interactive mode, simply run 
```
python3 ofgo.py
```
After running this, you will be prompted for necessary information. The first and main piece of information requested is the project repo URL or name. OFGO determines whether the input is a URL or name based on the presence of a period - no existing OSS-Fuzz projects had a period in their name. 

If you provide a valid git link (that is cloneable), OFGO will prompt for a build approach and the projects language. Any field that has a default field can be left as is - simply just press Enter. An example execution is shown below:

```
python ofgo.py
[15:57:09] [INFO] __main__: Running OFGO in interactive mode
Enter project repo URL or name: https://github.com/knotmyrealname/ofgo
Enter build approach: agent/template (default: template):         
Enter project language: python
Enter project maintainer email: danieldong1.618@gmail.com
...
```

This creates a new local project in the `gen-projects/{project_name}` folder, utilizing a template. Note that the template is not complete - you will need to add an entry into your project through the fuzz_test.`ext` file, where `ext` is the file extension for your project language and potentially make changes to the `Dockerfile` and `build.sh`. Once this is done, you can run the program again, now specifying either the original url or the project name (which should be the last element of the repo url: e.g. `https://github.com/knotmyrealname/ofgo -> ofgo` - check `gen-projects` to double check). We recommend using the project name as it doesn't involve any repo validation checks and is thus, faster. An example execution is shown below:

```
python ofgo.py
[00:14:45] [INFO] __main__: Running OFGO in interactive mode
Enter project repo URL or name: ofgo
Enter build approach: agent/template (default: template): 
[00:18:11] [INFO] __main__: Project already exists in OSS-Fuzz or in gen-projects.
Enter OpenAI model name (default: gpt-4o-mini): 
Enter OpenAI model temperature (default: 0.4): 
...
```

Here, OFGO was able to detect an existing project and requests OpenAI models and temperatures. You can leave these field blank, but we recommend utilizing gpt-5 models through our fork as they can be cheaper while providing higher performance (see our [README](./README.md#enabling-gpt-5-support) for more details). From here, OFGO checks for compilation and then runs OSS-Fuzz-Gen on the project using a custom script and puts the results of the generation in the cooresponding project folder in `gen-projects` labeled as `fuzz_harness_XX-XX.{ext}`. We suggest keeping an eye on the generation - OSS-Fuzz-Gen utilizes an iterative generation approach, feeding build failures back to the LLM for fixes. Sometimes the LLM may get stuck, especially for more complex projects, and utilize more API credits than you would like. Keep an eye on the output - phrases such as `===== ROUND 01 Recompile =====` and `</ASK PROMPT:ROUND 01>` indicate the LLM iteration number - this can get high if the LLM gets stuck, in which case you may want to terminate the program with a `CTRL + C`.

### LLM Generation
We have also provided an interface to an experimental OSS-Fuzz-Gen project that attempts to utilize an LLM to generate a harness. It can work, but for more complex projects, it can easily get stuck in generation or take a lot of iterations and thus cost a lot of API credits and time. To generate your harness with an LLM, you can just follow [Interactive Generation](#interactive-generation) and provide `agent` as the build approach. An important note is that the temperature is hardcoded to 0.4 within this experimental project, which means that GPT-5 models will not work. This may be a point of future work.

### Single-Command Generation
It is also possible to run Project Generation via a single command. With this, we recommend filling out all the fields to cover every possible scenario. The build, model, and temperature params have set defaults, so they are not necessary. 
```
python3 ofgo.py default \
  --repo <REPO_URL/PROJECT_NAME> \
  --email <MAINTAINER_EMAIL> \
  --build <agent/template> \
  --language <PROJECT_LANGUAGE> \
  --model <LLM_MODEL> \
  --temperature <LLM_MODEL_TEMPERATURE>
``` 

## Running only OSS-Fuzz-gen
You can run OSS-Fuzz-gen on an existing or generated project with the following command. The model and temperature values have defaults as the previous command so they are optional. 

```
python3 ofgo.py existing \
  --project <PROJECT_NAME> \
  --model <LLM_MODEL> \
  --temperature <LLM_MODEL_TEMPERATURE>
```

## Running OSS-Fuzz
You can run only OSS-Fuzz on a project using the following command. This pulls the latest images and runs all available fuzzers.

```
python3 ofgo.py coverage \
  --project <PROJECT_NAME>
```

## Running only Template-Based Generation
If you only want to generate a project without running OSS-Fuzz-Gen, you can run the following command to do so via a Template:

```
python3 ofgo.py template \
  --repo <REPO_URL/PROJECT_NAME> \
  --email <MAINTAINER_EMAIL> \
  --language <PROJECT_LANGUAGE>
```

## Running only Agent-Based Generation
If you only want to generate a project without running the main OSS-Fuzz-Gen harness generation, you can run the following command to do so via an LLM Agent:
```
python3 ofgo.py agent \
  --repo <REPO_URL/PROJECT_NAME> \
  --email <MAINTAINER_EMAIL> \
  --model <LLM_MODEL>
```

## Project Cleanup
If you want to remove a project from your local OFGO repository, you can utilize our cleanup feature. This removes the project from `gen-projects` and `oss-fuzz/projects` enabling you to reset and regenerate a template for the project. 

```
python3 ofgo.py remove \
  --project <PROJECT_NAME>
```

# Creating new seed corpuses using LLMs
Currently this functionality has not been implemented yet.
