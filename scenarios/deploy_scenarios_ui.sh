#!/bin/bash
# Deploy the public Scenarios demo with install.sh. Run on the host by the
# "Docker Scenarios UI CD" workflow (.github/workflows/scenarios-ui-deploy.yml).
#
# The host's $UI_PATH/.env must be a configured copy of .env.scenarios
# (OASIS_PUBLIC_DEMO=true, real passwords, SCENARIOS_PATH=$MODELS_PATH).
#
# Inputs (environment):
#   UI_PATH           OasisPythonUI checkout on the host
#   MODELS_PATH       Scenarios repository checkout (the scenario model data)
#   DEPLOY_UI         'true' to rebuild and restart the UI only
#   DEPLOY_ALL        'true' to redeploy the whole stack
#   WIPE              'true' (with DEPLOY_ALL) to delete all data first
#   UPDATE_SCENARIOS  'true' to update the scenario model data first
set -e

echo "DEPLOY_UI: $DEPLOY_UI"
echo "DEPLOY_ALL: $DEPLOY_ALL"
echo "UI_PATH: $UI_PATH"
echo "WIPE: $WIPE"
echo "UPDATE_SCENARIOS: $UPDATE_SCENARIOS"
echo "MODELS_PATH: $MODELS_PATH"

if [[ "$WIPE" = 'true' ]] && [[ "$DEPLOY_ALL" != 'true' ]]; then
  echo "WIPE without DEPLOY_ALL not allowed."
  exit 1
fi

cd "$UI_PATH"
if [[ ! -f .env ]] || ! grep -q '^OASIS_PUBLIC_DEMO=true' .env; then
  echo "ERROR: $UI_PATH/.env must be a configured copy of .env.scenarios (OASIS_PUBLIC_DEMO=true)."
  exit 1
fi

# Free disk space from old images and build cache (named volumes are kept)
docker system prune -f

git pull --ff-only

if [[ "$UPDATE_SCENARIOS" = 'true' ]]; then
  echo "Updating scenario model data in $MODELS_PATH"
  git -C "$MODELS_PATH" pull --ff-only
  ( cd "$MODELS_PATH"; ./get_s3_data_reduced.sh )
fi

if [[ "$DEPLOY_ALL" = 'true' ]]; then
  if [[ "$WIPE" = 'true' ]]; then
    echo "Removing the stack and all its data"
    ./install.sh --uninstall
  fi
  ./install.sh --yes --build-ui
elif [[ "$DEPLOY_UI" = 'true' ]]; then
  # Rebuild the UI image from this checkout, then recreate only the UI-side services
  set -a; source .env; set +a
  FILES="-f docker-compose.yml -f docker-compose.models.scenarios.yml -f docker-compose.ui.yml -f docker-compose.public.yml"
  [[ -n "${OASIS_ACME_EMAIL:-}" ]] && FILES="$FILES -f docker-compose.acme.yml"
  export OASIS_SERVICE_USERNAME_OR_ID="$OASIS_ADMIN_USER" OASIS_SERVICE_PASSWORD_OR_SECRET="$OASIS_ADMIN_PASS"
  docker compose $FILES build pythonui
  docker compose $FILES up -d --no-deps pythonui scenarios-setup scenarios-prune
fi

docker system prune -f
