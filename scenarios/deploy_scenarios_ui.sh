#!/bin/bash

echo "DEPLOY_UI: $DEPLOY_UI"
echo "DEPLOY_ALL: $DEPLOY_ALL"
echo "UI_PATH: $UI_PATH"
echo "WIPE: $WIPE"

if [[ "$WIPE" = 'true' ]] && [[ "$DEPLOY_ALL" = 'false' ]]; then
  echo "WIPE without DEPLOY_ALL not allowed."
  exit 1
fi

if [[ "$WIPE" = 'true' ]]; then
    printf "Deleting docker container:\n"
    set +e
    docker compose -f "$UI_PATH/oasis-scenarios-platform.yml" -f "$UI_PATH/oasis-scenarios-ui.yml" down --remove-orphans
    set -e
    printf "Deleting docker data: \n"
    docker volume ls | grep OasisData | awk 'BEGIN { FS = "[ \t\n]+" }{ print $2 }' | xargs -r docker volume rm
fi

if [[ "$DEPLOY_UI" = 'true' ]] && [[ "$DEPLOY_ALL" != 'true' ]]; then
  docker image pull coreoasis/oasis_scenarios
  docker compose -f "$UI_PATH/oasis-scenarios-ui.yml" up -d
fi

if [[ "$DEPLOY_ALL" = 'true' ]]; then
  docker pull coreoasis/model_worker:latest
  docker pull coreoasis/api_server:latest
  docker pull coreoasis/oasis_scenarios:latest
  docker compose -f "$UI_PATH/oasis-scenarios-platform.yml" up -d --no-build
  docker compose -f "$UI_PATH/oasis-scenarios-ui.yml" up -d --no-build
fi
