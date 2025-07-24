#!/bin/bash
export $(grep -v '^#' .env | xargs)

# Pull the latest images
set +e
docker pull ${WORKER_IMG-coreoasis/model_worker}:${VERS_WORKER:-latest}
docker pull ${SERVER_IMG-coreoasis/api_server}:${VERS_API:-latest}
docker pull ${SCENARIOS_UI_IMG-coreoasis/oasis_scenarios}:${VERS_API:-latest}
set -e

# Update
docker compose -f oasis-scenarios-platform.yml up -d
docker compose -f oasis-scenarios-ui.yml up -d
