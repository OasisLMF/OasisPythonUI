#!/bin/bash
set -e

# ============================================================================
# OasisPythonUI Installation Script
# ============================================================================
# Supports authentication types: simple, keycloak, authentik
# Auto-detects auth type from .env file and includes appropriate services.

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# ============================================================================
# Options
# ============================================================================

MODEL_SET_ARG=""
BUILD_UI=false
UNINSTALL=false

usage() {
    cat <<'USAGE'
Usage: ./install.sh [options]

  -m, --model-set           Name of model set to deploy, defaults to
                            'piwind'. Expects to find
                            `docker-compose.models.<models>.yml file and
                            optionally a get-<models>.sh script to deploy the
                            model in the root directory.
  --build-ui                Rebuild the UI docker container.
  -u, --uninstall           Bring the stack down and delete its volumes.
  -h, --help                Show this message.
USAGE
}

require_value() {
    if [ -z "$2" ]; then
        echo "ERROR: $1 needs a value" >&2
        exit 1
    fi
}

while [ $# -gt 0 ]; do
    case "$1" in
        -m|--model-set)   require_value "$1" "${2:-}"; MODEL_SET_ARG="$2"; shift 2 ;;
        --build-ui)    BUILD_UI=true; shift ;;
        -u|--uninstall) UNINSTALL=true; shift ;;
        -h|--help)     usage; exit 0 ;;
        *)             echo "ERROR: unknown option '$1'" >&2; usage >&2; exit 1 ;;
    esac
done

# ============================================================================
# Uninstall mode
# ============================================================================

if [ "$UNINSTALL" = true ]; then
    echo "Uninstalling Oasis platform (docker compose down only)..."

    # Every model set, so model workers come down whichever one was deployed
    MODEL_FILES=()
    for model_file in "$SCRIPT_DIR"/docker-compose.models.*.yml; do
        [ -f "$model_file" ] && MODEL_FILES+=(-f "$model_file")
    done

    set +e
    docker compose -f "$SCRIPT_DIR/docker-compose.yml" \
        -f "$SCRIPT_DIR/docker-compose.ui.yml" \
        -f "$SCRIPT_DIR/docker-compose.keycloak.yml" \
        -f "$SCRIPT_DIR/docker-compose.authentik.yml" \
        "${MODEL_FILES[@]}" \
        down --remove-orphans -v 2>/dev/null
    # Also try old files in case of migration
    docker compose -f "$SCRIPT_DIR/oasis-platform.yml" \
        -f "$SCRIPT_DIR/oasis-ui.yml" \
        down --remove-orphans -v 2>/dev/null
    set -e

    echo "Uninstall complete."
    exit 0
fi

# ============================================================================
# Load configuration from .env
# ============================================================================

if [ ! -f "$SCRIPT_DIR/.env" ]; then
    echo "ERROR: .env file not found!"
    echo ""
    echo "Create one from the examples:"
    echo "  cp .env.simple .env      # Simple JWT authentication"
    echo "  cp .env.keycloak .env    # Keycloak OIDC"
    echo "  cp .env.authentik .env   # Authentik OIDC"
    exit 1
fi

set -a
source "$SCRIPT_DIR/.env"
set +a


# ============================================================================
# Auto-detect Docker socket if not set
# ============================================================================

if [ -z "$DOCKER_SOCK" ]; then
    # Default to /var/run/docker.sock - Docker Desktop provides this path
    # transparently to containers even if the host socket is elsewhere.
    export DOCKER_SOCK=/var/run/docker.sock
elif [ ! -S "$DOCKER_SOCK" ]; then
    echo "WARNING: DOCKER_SOCK=$DOCKER_SOCK does not exist or is not a socket"
    echo "  Falling back to /var/run/docker.sock"
    export DOCKER_SOCK=/var/run/docker.sock
fi

# ============================================================================
# Resolve the model compose files
# ============================================================================

MODEL_SET_NAME="${MODEL_SET_ARG:-${MODEL_SET:-piwind}}"
MODEL_COMPOSE_FILE="$SCRIPT_DIR/docker-compose.models.$MODEL_SET_NAME.yml"
MODEL_SETUP_SCRIPT="$SCRIPT_DIR/get-$MODEL_SET_NAME.sh"
if [ ! -f "$MODEL_COMPOSE_FILE" ]; then
    echo "ERROR: no model set '$MODEL_SET_NAME': $(basename "$MODEL_COMPOSE_FILE") not found"
    echo ""
    exit 1
fi

echo "========================================"
echo " OasisPythonUI Installer"
echo "========================================"
echo ""
echo "  Auth type:     $API_AUTH_TYPE"
echo "  Model set:     $MODEL_SET_NAME"
echo "  Hostname:      $OASIS_UI_HOSTNAME"
echo "  Protocol:      $OASIS_PROTOCOL"
echo "  Docker socket: $DOCKER_SOCK"
echo ""

# ============================================================================
# Validate configuration
# ============================================================================

echo "--- Validating configuration ---"
bash "$SCRIPT_DIR/scripts/validate-config.sh"
echo ""

# ============================================================================
# Set service account credentials based on auth type
# ============================================================================

echo "--- Configuring service credentials ---"

if [ "$API_AUTH_TYPE" = "simple" ]; then
    export OASIS_SERVICE_USERNAME_OR_ID="$OASIS_ADMIN_USER"
    export OASIS_SERVICE_PASSWORD_OR_SECRET="$OASIS_ADMIN_PASS"
    export OASIS_USE_OIDC=""
    echo "  -> Simple auth: using admin credentials for service account"

elif [ "$API_AUTH_TYPE" = "keycloak" ]; then
    export OASIS_SERVER_OIDC_SERVICE_CLIENT_NAME="$OASIS_SERVICE_CLIENT_NAME"
    export OASIS_SERVER_OIDC_SERVICE_CLIENT_SECRET="$OASIS_SERVICE_CLIENT_SECRET"
    export OASIS_SERVER_OIDC_CLIENT_NAME="$OIDC_KEYCLOAK_CLIENT_NAME"
    export OASIS_SERVER_OIDC_CLIENT_SECRET="$OIDC_KEYCLOAK_CLIENT_SECRET"
    export OASIS_SERVER_OIDC_ENDPOINT="${OASIS_PROTOCOL}://${OASIS_UI_HOSTNAME}/auth/realms/oasis/protocol/openid-connect/"
    export OASIS_SERVICE_USERNAME_OR_ID="$OASIS_SERVICE_CLIENT_NAME"
    export OASIS_SERVICE_PASSWORD_OR_SECRET="$OASIS_SERVICE_CLIENT_SECRET"
    export OASIS_USE_OIDC="true"
    echo "  -> Keycloak auth: using OIDC client credentials"
    echo "  -> OIDC endpoint: $OASIS_SERVER_OIDC_ENDPOINT"

elif [ "$API_AUTH_TYPE" = "authentik" ]; then
    export OASIS_SERVER_OIDC_SERVICE_CLIENT_NAME="$OASIS_SERVICE_CLIENT_NAME"
    export OASIS_SERVER_OIDC_SERVICE_CLIENT_SECRET="$OASIS_SERVICE_CLIENT_SECRET"
    export OASIS_SERVER_OIDC_CLIENT_NAME="$OIDC_AUTHENTIK_CLIENT_NAME"
    export OASIS_SERVER_OIDC_CLIENT_SECRET="$OIDC_AUTHENTIK_CLIENT_SECRET"
    export OASIS_SERVER_OIDC_ENDPOINT="${OASIS_PROTOCOL}://${OASIS_UI_HOSTNAME}/authentik/application/o/"
    export OASIS_SERVICE_USERNAME_OR_ID="$OASIS_SERVICE_CLIENT_NAME"
    export OASIS_SERVICE_PASSWORD_OR_SECRET="$OASIS_SERVICE_CLIENT_SECRET"
    export OASIS_USE_OIDC="true"
    echo "  -> Authentik auth: using OIDC client credentials"
    echo "  -> OIDC endpoint: $OASIS_SERVER_OIDC_ENDPOINT"
fi

echo ""

# ============================================================================
# Process OIDC templates (if applicable)
# ============================================================================

if [ "$API_AUTH_TYPE" = "keycloak" ]; then
    echo "--- Processing Keycloak templates ---"
    bash "$SCRIPT_DIR/oidc/keycloak/process-keycloak-templates.sh"
    echo ""
elif [ "$API_AUTH_TYPE" = "authentik" ]; then
    echo "--- Processing Authentik templates ---"
    bash "$SCRIPT_DIR/oidc/authentik/process-authentik-templates.sh"
    echo ""
fi

# ============================================================================
# Build compose file list
# ============================================================================

COMPOSE_FILES="-f $SCRIPT_DIR/docker-compose.yml -f $MODEL_COMPOSE_FILE -f $SCRIPT_DIR/docker-compose.ui.yml"

if [ "$API_AUTH_TYPE" = "keycloak" ]; then
    COMPOSE_FILES="$COMPOSE_FILES -f $SCRIPT_DIR/docker-compose.keycloak.yml"
    echo "  -> Including Keycloak services"
elif [ "$API_AUTH_TYPE" = "authentik" ]; then
    COMPOSE_FILES="$COMPOSE_FILES -f $SCRIPT_DIR/docker-compose.authentik.yml"
    echo "  -> Including Authentik services"
fi

echo "  -> Compose files: $COMPOSE_FILES"
echo ""


# ============================================================================
# Get model data
# ============================================================================
echo "--- Retrieving Model Data ---"

if [ -f "$MODEL_SETUP_SCRIPT" ]; then
    bash "$MODEL_SETUP_SCRIPT"
else
    echo "  -> No get-$MODEL_NAME.sh, expecting the $MODEL_NAME model data to be in place"
fi
echo ""

# ============================================================================
# Check for previous install
# ============================================================================

EXISTING_CONTAINERS=$(docker compose $COMPOSE_FILES ps -q 2>/dev/null | wc -l)

if [ "$EXISTING_CONTAINERS" -gt 0 ]; then
    MSG="Previous installation detected. Redeploy? (existing data will be preserved)"
    while true; do
        read -r -n 1 -p "${MSG} [y/n]: " REPLY
        case $REPLY in
            [yY]) echo ; break ;;
            [nN]) echo ; echo "-- Aborted --"; exit 1 ;;
            *) printf " \033[31m %s \n\033[0m" "invalid input" ;;
        esac
    done
fi

# ============================================================================
# Pull images
# ============================================================================

echo "--- Pulling images ---"

set +e
docker pull --ignore-pull-failures "${SERVER_IMG:-coreoasis/api_server}:${VERS_API:-latest}"
docker pull --ignore-pull-failures "${WORKER_IMG:-coreoasis/model_worker}:${VERS_WORKER:-latest}"
set -e

echo ""

# ============================================================================
# Build UI if necessary
# ============================================================================

if [ "$BUILD_UI" = true ]; then
    echo "  -> Building UI image"
    docker compose $COMPOSE_FILES build --no-cache pythonui
else
    echo "  -> Pulling UI image ${PYTHONUI_IMG:-coreoasis/oasispythonui_app}:${VERS_UI:-latest}"
    set +e
    docker pull --ignore-pull-failures "${PYTHONUI_IMG:-coreoasis/oasispythonui_app}:${VERS_UI:-latest}"
    set -e
fi

# ============================================================================
# Deploy services
# ============================================================================

echo "--- Deploying services ---"

# Start all services
docker compose $COMPOSE_FILES up -d

echo ""

# ============================================================================
# Wait for health checks
# ============================================================================

echo "--- Waiting for services to be healthy ---"

# Wait for core services
echo "  -> Waiting for server..."
docker compose $COMPOSE_FILES exec -T server sh -c 'for i in $(seq 1 60); do curl -sf http://localhost:8000/healthcheck/ > /dev/null 2>&1 && exit 0; sleep 5; done; exit 1' || {
    echo "  WARNING: Server health check timed out. Check logs with: docker compose $COMPOSE_FILES logs server"
}

if [ "$API_AUTH_TYPE" = "keycloak" ]; then
    echo "  -> Waiting for Keycloak (this may take 2-3 minutes on first start)..."
    timeout 180 bash -c "while ! docker compose $COMPOSE_FILES ps keycloak 2>/dev/null | grep -q 'healthy'; do sleep 10; done" 2>/dev/null || {
        echo "  WARNING: Keycloak health check timed out. Check logs with: docker compose $COMPOSE_FILES logs keycloak"
    }
elif [ "$API_AUTH_TYPE" = "authentik" ]; then
    echo "  -> Waiting for Authentik..."
    timeout 180 bash -c "while ! docker compose $COMPOSE_FILES ps authentik-server 2>/dev/null | grep -q 'healthy'; do sleep 10; done" 2>/dev/null || {
        echo "  WARNING: Authentik health check timed out. Check logs with: docker compose $COMPOSE_FILES logs authentik-server"
    }
fi

echo ""

# ============================================================================
# Summary
# ============================================================================

echo "========================================"
echo " Deployment Complete!"
echo "========================================"
echo ""
echo "  Auth type:     $API_AUTH_TYPE"
echo "  Hostname:      $OASIS_UI_HOSTNAME"
echo ""
echo "  Access Points (via Traefik on port 80):"
echo "    UI:          http://${OASIS_UI_HOSTNAME}/"
echo "    API:         http://${OASIS_UI_HOSTNAME}/api/"
echo "    API Docs:    http://${OASIS_UI_HOSTNAME}/api/swagger/"

if [ "$API_AUTH_TYPE" = "keycloak" ]; then
    echo "    Keycloak:    http://${OASIS_UI_HOSTNAME}/auth/admin/"
    echo "                 (${KEYCLOAK_ADMIN_USER} / ${KEYCLOAK_ADMIN_PASSWORD})"
elif [ "$API_AUTH_TYPE" = "authentik" ]; then
    echo "    Authentik:   http://${OASIS_UI_HOSTNAME}/authentik/"
    echo "                 (akadmin / ${AUTHENTIK_BOOTSTRAP_PASSWORD})"
fi

if [ "$API_AUTH_TYPE" = "simple" ]; then
    echo ""
    echo "  Login:         ${OASIS_ADMIN_USER} / ${OASIS_ADMIN_PASS}"
fi

echo ""
echo "  Logs:          docker compose $COMPOSE_FILES logs -f"
echo "  Stop:          docker compose $COMPOSE_FILES down"
echo ""
