#!/bin/bash
# Configuration validator for OasisPythonUI
# Validates .env file before deployment

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

ERRORS=0
WARNINGS=0

echo "Validating configuration..."

# ============================================================================
# Check Required Variables
# ============================================================================

# Check API_AUTH_TYPE
if [ -z "$API_AUTH_TYPE" ]; then
    echo "ERROR: API_AUTH_TYPE is not set"
    ERRORS=$((ERRORS+1))
elif [ "$API_AUTH_TYPE" != "simple" ] && [ "$API_AUTH_TYPE" != "keycloak" ] && [ "$API_AUTH_TYPE" != "authentik" ]; then
    echo "ERROR: API_AUTH_TYPE must be 'simple', 'keycloak', or 'authentik' (got: $API_AUTH_TYPE)"
    ERRORS=$((ERRORS+1))
else
    echo "OK API_AUTH_TYPE: $API_AUTH_TYPE"
fi

# Check hostname
if [ -z "$OASIS_UI_HOSTNAME" ]; then
    echo "ERROR: OASIS_UI_HOSTNAME is not set"
    ERRORS=$((ERRORS+1))
else
    echo "OK OASIS_UI_HOSTNAME: $OASIS_UI_HOSTNAME"
fi

# Check protocol
if [ -z "$OASIS_PROTOCOL" ]; then
    echo "ERROR: OASIS_PROTOCOL is not set"
    ERRORS=$((ERRORS+1))
elif [ "$OASIS_PROTOCOL" != "http" ] && [ "$OASIS_PROTOCOL" != "https" ]; then
    echo "ERROR: OASIS_PROTOCOL must be 'http' or 'https' (got: $OASIS_PROTOCOL)"
    ERRORS=$((ERRORS+1))
else
    echo "OK OASIS_PROTOCOL: $OASIS_PROTOCOL"
fi

# Check compose project name
if [ -z "$COMPOSE_PROJECT_NAME" ]; then
    echo "WARNING: COMPOSE_PROJECT_NAME is not set (will use directory name)"
    WARNINGS=$((WARNINGS+1))
else
    echo "OK COMPOSE_PROJECT_NAME: $COMPOSE_PROJECT_NAME"
fi

# ============================================================================
# Check Auth-Specific Configuration
# ============================================================================

if [ "$API_AUTH_TYPE" = "keycloak" ]; then
    echo ""
    echo "Checking Keycloak configuration..."

    # Check users file
    if [ ! -f "$PROJECT_ROOT/oidc/keycloak/users.yaml" ]; then
        echo "ERROR: oidc/keycloak/users.yaml not found"
        ERRORS=$((ERRORS+1))
    else
        echo "OK users.yaml found"
    fi

    # Check template files
    if [ ! -f "$PROJECT_ROOT/oidc/keycloak/oasis-realm.json.template" ]; then
        echo "ERROR: oidc/keycloak/oasis-realm.json.template not found"
        ERRORS=$((ERRORS+1))
    else
        echo "OK realm template found"
    fi

    if [ ! -f "$PROJECT_ROOT/oidc/keycloak/oasis-realm-user.json.template" ]; then
        echo "ERROR: oidc/keycloak/oasis-realm-user.json.template not found"
        ERRORS=$((ERRORS+1))
    else
        echo "OK user template found"
    fi

    # Check processing script
    if [ ! -f "$PROJECT_ROOT/oidc/keycloak/process-keycloak-templates.sh" ]; then
        echo "ERROR: oidc/keycloak/process-keycloak-templates.sh not found"
        ERRORS=$((ERRORS+1))
    else
        echo "OK processing script found"
    fi

    # Check required variables
    if [ -z "$KEYCLOAK_ADMIN_USER" ]; then
        echo "ERROR: KEYCLOAK_ADMIN_USER is not set"
        ERRORS=$((ERRORS+1))
    fi

    if [ -z "$OIDC_KEYCLOAK_CLIENT_NAME" ]; then
        echo "ERROR: OIDC_KEYCLOAK_CLIENT_NAME is not set"
        ERRORS=$((ERRORS+1))
    fi

elif [ "$API_AUTH_TYPE" = "authentik" ]; then
    echo ""
    echo "Checking Authentik configuration..."

    # Check users file
    if [ ! -f "$PROJECT_ROOT/oidc/authentik/users.yaml" ]; then
        echo "ERROR: oidc/authentik/users.yaml not found"
        ERRORS=$((ERRORS+1))
    else
        echo "OK users.yaml found"
    fi

    # Check template files
    if [ ! -f "$PROJECT_ROOT/oidc/authentik/oasis-blueprint.yaml.template" ]; then
        echo "ERROR: oidc/authentik/oasis-blueprint.yaml.template not found"
        ERRORS=$((ERRORS+1))
    else
        echo "OK blueprint template found"
    fi

    if [ ! -f "$PROJECT_ROOT/oidc/authentik/oasis-users-blueprint.yaml.template" ]; then
        echo "ERROR: oidc/authentik/oasis-users-blueprint.yaml.template not found"
        ERRORS=$((ERRORS+1))
    else
        echo "OK user template found"
    fi

    # Check processing script
    if [ ! -f "$PROJECT_ROOT/oidc/authentik/process-authentik-templates.sh" ]; then
        echo "ERROR: oidc/authentik/process-authentik-templates.sh not found"
        ERRORS=$((ERRORS+1))
    else
        echo "OK processing script found"
    fi

    # Check required variables
    if [ -z "$AUTHENTIK_BOOTSTRAP_USER" ]; then
        echo "ERROR: AUTHENTIK_BOOTSTRAP_USER is not set"
        ERRORS=$((ERRORS+1))
    fi

    if [ -z "$OIDC_AUTHENTIK_CLIENT_NAME" ]; then
        echo "ERROR: OIDC_AUTHENTIK_CLIENT_NAME is not set"
        ERRORS=$((ERRORS+1))
    fi

elif [ "$API_AUTH_TYPE" = "simple" ]; then
    echo ""
    echo "Checking Simple auth configuration..."

    if [ -z "$OASIS_ADMIN_USER" ]; then
        echo "ERROR: OASIS_ADMIN_USER is not set"
        ERRORS=$((ERRORS+1))
    fi

    if [ -z "$OASIS_ADMIN_PASS" ]; then
        echo "WARNING: OASIS_ADMIN_PASS is not set"
        WARNINGS=$((WARNINGS+1))
    fi
fi

# ============================================================================
# Check Database Configuration
# ============================================================================

echo ""
echo "Checking database configuration..."

if [ -z "$OASIS_SERVER_DB_NAME" ]; then
    echo "WARNING: OASIS_SERVER_DB_NAME is not set"
    WARNINGS=$((WARNINGS+1))
else
    echo "OK OASIS_SERVER_DB_NAME: $OASIS_SERVER_DB_NAME"
fi

if [ -z "$OASIS_CELERY_DB_NAME" ]; then
    echo "WARNING: OASIS_CELERY_DB_NAME is not set"
    WARNINGS=$((WARNINGS+1))
else
    echo "OK OASIS_CELERY_DB_NAME: $OASIS_CELERY_DB_NAME"
fi

# ============================================================================
# Summary
# ============================================================================

echo ""
echo "========================================"

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo "Configuration validation passed!"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo "Configuration has $WARNINGS warning(s) but is valid"
    exit 0
else
    echo "Configuration validation failed with $ERRORS error(s) and $WARNINGS warning(s)"
    exit 1
fi
