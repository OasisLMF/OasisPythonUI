#!/bin/bash
#
# Put the scenario model data in place for docker-compose.models.scenarios.yml.
#
# Run by install.sh when the scenarios model set is selected, and safe to run
# on its own. Idempotent: it clones the Scenarios repository and pulls down the
# model files once, then no-ops.
#
# Reads SCENARIOS_PATH from the environment (install.sh exports it from .env):
# the directory the scenario workers mount their model data from.

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

SCENARIOS_REPO="https://github.com/OasisLMF/Scenarios.git"
# One of the model directories the compose file mounts, used to tell whether
# the model files have been pulled down from s3 yet
SENTINEL_MODEL="ImpactForecasting/MAEQ/1.0.0"

if [ -z "$SCENARIOS_PATH" ]; then
    echo "ERROR: SCENARIOS_PATH is not set."
    echo "  Set it in .env to the directory the scenario models live in, for"
    echo "  example SCENARIOS_PATH=/home/ubuntu/Scenarios. This script clones"
    echo "  $SCENARIOS_REPO there if it is missing."
    exit 1
fi

# The scenarios set runs PiWind alongside the scenario models
bash "$SCRIPT_DIR/get-piwind.sh"

if [ -d "$SCENARIOS_PATH" ]; then
  echo "  -> Scenario models already checked out at $SCENARIOS_PATH"
else
    echo "  -> Cloning scenario models into $SCENARIOS_PATH"
    git clone --depth 1 "$SCENARIOS_REPO" "$SCENARIOS_PATH"
fi

if [ -d "$SCENARIOS_PATH/$SENTINEL_MODEL" ]; then
    echo "  -> Scenario model files already downloaded"
    exit 0
fi

if [ ! -x "$SCENARIOS_PATH/get_s3_data_reduced.sh" ]; then
    echo "ERROR: $SCENARIOS_PATH/get_s3_data_reduced.sh not found."
    exit 1
fi

echo "  -> Downloading scenario model files (this takes a while)"
( cd "$SCENARIOS_PATH" && ./get_s3_data_reduced.sh )
