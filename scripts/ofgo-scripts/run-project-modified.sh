#!/bin/bash
# Copyright 2024 Google LLC
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

## This is an modified version of the script inside of oss-fuzz-gen/scripts/run-new-oss-fuzz-project.sh

OSS_FUZZ_GEN_DIR=${1}
OSS_FUZZ_DIR=${2}
FI_DIR=${3}
BENCHMARK_HEURISTICS=${4}
PROJECT=${5}
HARNESSES_PER_PROJECT=${6}
NUM_SAMPLES=${7}
OSS_FUZZ_GEN_MODEL=${8}
TEMPERATURE=${9}
WORK_DIR=${10}

# Specifify OSS-Fuzz-gen to not clean up the OSS-Fuzz project. Enabling
# this will cause all changes in the OSS-Fuzz repository to be nullified.
export OFG_CLEAN_UP_OSS_FUZZ=0

echo "Targeting project: $5"

# Generate fresh introspector reports that OFG can use as seed for auto
# generation.
echo "Creating introspector reports"
cd ${OSS_FUZZ_DIR}

python3 $FI_DIR/oss_fuzz_integration/runner.py \
  introspector $PROJECT 1 --disable-webserver
  # Reset is necessary because some project exeuction
  # could break the display encoding which affect
  # the later oss-fuzz-gen execution.
reset

# Shut down the existing webapp if it's running
curl --silent http://localhost:8080/api/shutdown || true

# Create Fuzz Introspector's webserver DB
echo "[+] Creating the webapp DB"
cd $FI_DIR/tools/web-fuzzing-introspection/app/static/assets/db/
python3 ./web_db_creator_from_summary.py \
    --local-oss-fuzz ${OSS_FUZZ_DIR}

# Start webserver
echo "Shutting down server in case it's running"
curl --silent http://localhost:8080/api/shutdown || true

echo "[+] Launching FI webapp"
cd $FI_DIR/tools/web-fuzzing-introspection/app/
FUZZ_INTROSPECTOR_LOCAL_OSS_FUZZ=${OSS_FUZZ_DIR} \
  python3 ./main.py >> /dev/null &

# Wait for the webapp to start.
SECONDS=5
while true
do
  # Checking if exists
  MSG=$(curl -v --silent 127.0.0.1:8080 2>&1 | grep "Fuzzing" | wc -l)
  if [[ $MSG > 0 ]]; then
    echo "Found it"
    break
  fi
  echo "- Waiting for webapp to load. Sleeping ${SECONDS} seconds."
  sleep ${SECONDS}
done

# Run OSS-Fuzz-gen on the projects
echo "[+] Running OSS-Fuzz-gen experiment"
cd ${OSS_FUZZ_GEN_DIR}

# Hack to ensure no complaints from: https://github.com/google/oss-fuzz-gen/blob/54d4acc02ef5b15288f1e0718f00bfbf8f5024c5/experiment/oss_fuzz_checkout.py#L117-L123
mkdir -p ${OSS_FUZZ_DIR}/venv

# Run OSS-Fuzz-gen
# - Generate benchmarks
# - Use a local version version of OSS-Fuzz (the one in /work/oss-fuzz)
LLM_NUM_EVA=4 LLM_NUM_EXP=4 ./run_all_experiments.py \
    --model=$OSS_FUZZ_GEN_MODEL \
    --generate-benchmarks ${BENCHMARK_HEURISTICS} \
    --generate-benchmarks-projects ${PROJECT} \
    --generate-benchmarks-max ${HARNESSES_PER_PROJECT} \
    --oss-fuzz-dir ${OSS_FUZZ_DIR} \
    --temperature ${TEMPERATURE} \
    --work-dir ${WORK_DIR} \
    --num-samples ${NUM_SAMPLES} \
    --introspector-endpoint http://127.0.0.1:8080/api 

echo "Shutting down started webserver"
curl --silent http://localhost:8080/api/shutdown || true
