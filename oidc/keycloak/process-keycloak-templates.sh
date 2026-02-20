#!/bin/bash
set -e

# ============================================================================
# Keycloak Template Processor
# ============================================================================
# Processes Keycloak realm and user templates with ___VAR___ placeholders
# Mimics Helm template processing from OasisPlatform Kubernetes deployment

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
TEMPLATE_DIR="$SCRIPT_DIR"
OUTPUT_DIR="$SCRIPT_DIR/generated"
USERS_FILE="$SCRIPT_DIR/users.yaml"

# Ensure required tools are available
if ! command -v jq &> /dev/null; then
    echo "  ERROR: jq is required but not installed"
    exit 1
fi

if ! command -v uuidgen &> /dev/null; then
    echo "  ERROR: uuidgen is required but not installed"
    exit 1
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"

# ============================================================================
# Parse Users YAML
# ============================================================================

echo "  -> Parsing users from users.yaml"

# Convert YAML to JSON
# Try yq first, fallback to python
if command -v yq &> /dev/null; then
    USERS_JSON=$(yq eval '.users' "$USERS_FILE" -o=json)
else
    # Fallback to python
    USERS_JSON=$(python3 -c "
import yaml, json, sys
with open('$USERS_FILE') as f:
    data = yaml.safe_load(f)
    print(json.dumps(data['users']))
")
fi

USER_COUNT=$(echo "$USERS_JSON" | jq '. | length')
echo "  -> Found $USER_COUNT user(s)"

if [ "$USER_COUNT" -eq 0 ]; then
    echo "  ERROR: No users defined in users.yaml"
    exit 1
fi

# ============================================================================
# Generate User JSON Entries
# ============================================================================

echo "  -> Generating user entries from template"

USER_TEMPLATE=$(cat "$TEMPLATE_DIR/oasis-realm-user.json.template")
USER_ENTRIES=()

# Process each user
while IFS= read -r user; do
    username=$(echo "$user" | jq -r '.username')
    password=$(echo "$user" | jq -r '.password')
    is_admin=$(echo "$user" | jq -r '.admin')

    echo "     - Processing user: $username"

    # Generate UUID for user
    uuid=$(uuidgen | tr '[:upper:]' '[:lower:]')

    # Build roles and groups
    roles='"default-roles-oasis"'
    groups=''

    if [ "$is_admin" = "true" ]; then
        groups='"admin"'
    fi

    # Replace variables in template
    user_entry="$USER_TEMPLATE"
    user_entry="${user_entry//___UUID___/$uuid}"
    user_entry="${user_entry//___USERNAME___/$username}"
    user_entry="${user_entry//___PASSWORD___/$password}"
    user_entry="${user_entry//___ROLES___/$roles}"
    user_entry="${user_entry//___GROUPS___/$groups}"

    USER_ENTRIES+=("$user_entry")

done < <(echo "$USERS_JSON" | jq -c '.[]')

# Join user entries with commas - use jq to properly format as JSON array
if [ ${#USER_ENTRIES[@]} -eq 1 ]; then
    # Single user - no comma needed
    USERS_JSON_ARRAY="${USER_ENTRIES[0]}"
else
    # Multiple users - join with comma and newline
    USERS_JSON_ARRAY=$(printf '%s,\n' "${USER_ENTRIES[@]}" | sed '$s/,$//')
fi

echo "  -> Generated ${#USER_ENTRIES[@]} user entry(ies)"

# ============================================================================
# Process Main Realm Template
# ============================================================================

echo "  -> Processing realm template"

REALM_TEMPLATE=$(cat "$TEMPLATE_DIR/oasis-realm.json.template")

# Replace ___USERS___ placeholder (the placeholder is quoted: "___USERS___")
REALM_JSON="${REALM_TEMPLATE//\"___USERS___\"/$USERS_JSON_ARRAY}"

# Build redirect base URL
REDIRECT_BASE="${OASIS_PROTOCOL}://${OASIS_UI_HOSTNAME}"
echo "  -> Using redirect base: $REDIRECT_BASE"

# Replace hostname placeholders (if any exist in the template)
REALM_JSON="${REALM_JSON//___OASIS_PROTOCOL___/$OASIS_PROTOCOL}"
REALM_JSON="${REALM_JSON//___OASIS_UI_HOSTNAME___/$OASIS_UI_HOSTNAME}"
REALM_JSON="${REALM_JSON//___REDIRECT_BASE___/$REDIRECT_BASE}"

# ============================================================================
# Write Output
# ============================================================================

OUTPUT_FILE="$OUTPUT_DIR/oasis-realm.json"
echo "$REALM_JSON" > "$OUTPUT_FILE"

echo "  -> Realm configuration written to: $OUTPUT_FILE"

# ============================================================================
# Validate JSON
# ============================================================================

echo "  -> Validating generated JSON"

if ! jq empty "$OUTPUT_FILE" 2>/dev/null; then
    echo "  ERROR: Generated JSON is invalid!"
    echo "  -> Check syntax errors in template or processing logic"
    exit 1
fi

echo "  OK Generated JSON is valid"
echo "  OK Keycloak template processing complete!"
