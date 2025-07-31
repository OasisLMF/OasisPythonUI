#!/bin/bash

echo "DEPLOY_UI: $DEPLOY_UI"
echo "UI_PATH: $UI_PATH"

if [ "$DEPLOY_UI" = 'true' ]; then
  docker image pull coreoasis/oasis_scenarios
  docker compose -f "$UI_PATH/oasis-scenarios-ui.yml" up -d
fi
