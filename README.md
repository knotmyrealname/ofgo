# Check the ddong2/cleanup branch for the latest code - it's overall more usable, but it's possible that there may still be broken code somewhere
# OFGO: An Easy way to get Started with Fuzzing
This collection of scripts serves as an entry into fuzzing with OSS-Fuzz, simplifying the whole process into one command line argument. We utilize existing functionality within OSS-Fuzz and OSS-Fuzz gen to make this happen to maximize compatibility, with some custom code to enable automatic corpus generation. Note that, although we will be generating fuzzing harnesses, you will still have to **manually** add them to OSS-Fuzz via a pull request.

**NOTE: From our testing, OSS-Fuzz and OSS-Fuzz-gen DOES NOT work with Windows, and the same will be true for OFGO. This entire stack is designed for Linux - any support for other operating systems will be purely coincidental.**

## What is Fuzzing? 
At a high level, fuzzing is an automated software testing technique that runs programs with a large amount of mutated and randomly generated data to attempt to induce a fail condition/crash (which may lead to a bug/security vulnerability). 

## What is a Fuzz Harness?
Fuzz harnesses are essentially programs that connects a fuzzing engine to a target program, setting up the work environment and translating the engine input into data that can be interpreted by the target program. Within Fuzz harnesses are fuzz targets, individual files that contain instructions for fuzzing specific parts of the target program.

## What is a Seed Corpus?
A seed corpus is the starting data for the fuzzer - generally valid input. This starting data will then be mutated by the fuzzing engine in many different ways in an attempt to cause a failure condition. Although it is generally fine to run fuzzing engines with blank corpuses, a manually curated corpus will generally enable the fuzzing engine to achieve higher coverage results. The size of a seed corpus should be minimized, ideally, as it is expanded by the fuzzing engine to many orders of magnitude greater than its original size, and can take up unnecessary space and computational power. 

## What is OSS-Fuzz?
OSS-Fuzz is a project created by Google for continuously fuzzing open source software. They accept projects through Github pull requests ([docs](https://google.github.io/oss-fuzz/getting-started/accepting-new-projects/)), where they initially expect only a project.yaml (created in oss-fuzz/projects/{your-project}). Before a project is submitted to OSS-Fuzz, it must be shown that it either has a significant user base or is critical to the global IT infrastructure (you can do this in your pull request - check pull request history to see examples). When a project is submitted, Google will run OSS-Fuzz on it every few days, with build logs provided on [this website](https://oss-fuzz-build-logs.storage.googleapis.com/index.html). Additionally, the most up-to-date coverage reports and various other statistics can be found on the [Introspector Website](https://introspector.oss-fuzz.com/).

## What is OSS-Fuzz-gen?
OSS-Fuzz-gen is a framework created by Google for helping automate the Fuzz harness generation process, by generating fuzz targets, with the help of LLMs. It does this by prompting the LLM to generate a fuzzing harness, providing it with build logs if the harness generator fails to build, until the LLM is able to generate a working fuzzing harness.

## Setup
### Docker
OSS-Fuzz uses docker images to build and run fuzzers. Installation instructions for various Linux distributions may be found on the [Docker website](https://docs.docker.com/engine/install/)

### Installation
These installation instructions assume that python is installed and on path (with the exception of conda).

1. **Clone the Necessary Repositories** into the desired directory
```
git clone https://github.com/knotmyrealname/ofgo
cd ofgo
git submodule update --init --recursive
```
2. **Set up Python Environment** - This step is not strictly necessary, but highly recommended to maintain a clean working environment. From our testing, python 3.11 is required to run OSS-Fuzz and OSS-Fuzz-gen. 

 - **With Conda**
   - [Conda Installation for Linux](https://docs.conda.io/projects/conda/en/latest/user-guide/install/linux.html)
   - Setup: `conda create -n {name} python=3.11`
     - Replace {name} with the name of your conda environment
   - Activation: `conda activate {name}`
   - Deactivation: `conda deactivate`
 - **With venv**
   - Venv Installation: `pip install virtualenv`
   - Setup: `python3.11 -m venv venv`
   - Activation: `source venv/bin/activate`
   - Deactivation: `deactivate`

3. **Install Necessary Dependencies** - Make sure to do this while the `conda` or `venv` environment is activated

```
pip install -r requirements.txt
pip install -r oss-fuzz-gen/requirements.txt
```

### LLM Key Setup
OFGO only officially supports OpenAI's ChatGPT API for LLM-based generation, to simplify the workspace. We do not offically support Google's vertex models (listed [here](https://github.com/google/oss-fuzz-gen/blob/main/USAGE.md)), as they require a gcloud account, but there's no reason they wouldn't work if set up properly.

To set up your LLM key, simply export your OpenAI API key as an environmental variable:

```
export OPENAI_API_KEY=<your-API-key>
```

## Usage
Check out our detailed [usage guide](./USAGE.md) for documentation on available commands

## Understanding Output
TODO

## Enabling GPT-5 Support
By default, OSS-Fuzz-gen does not support OpenAI's GPT-5 models. If you would like to work with GPT-5, we have provided a fork with a patch to enable GPT-5. Note that GPT-5 will only work with a temperature of 1 (set by `--temperature 1`). To enable this patch, run the following commands:

```
git submodule set-url -- oss-fuzz-gen https://github.com/knotmyrealname/oss-fuzz-gen
git submodule update --remote --recursive
```
Note that this may not be up-to-date with the latest version of OSS-Fuzz-gen. If this is the case, feel free to open up an issue and we will attempt to update the fork as soon as possible. 

Currently, the following GPT-5 models are supported:
 - gpt-5
 - gpt-5-mini
 - gpt-5-nano

### Open Source LLMs
If there is enough interest, we may look to update our fork to enable the use of Open Source LLMs through HuggingFace. We suspect these models will produce inferior results, compared to large closed-source models, but that will be a topic of future research. 

## Contact
For questions, comments, or support, please create a Github issue. A contributor will respond whenever they are available

TODO - create issue template
