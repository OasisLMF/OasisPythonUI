#!/bin/bash
set -e

# ============================================================================
# Authentik Template Processor
# ============================================================================
# Processes Authentik blueprint and user templates with ___VAR___ placeholders
# Mimics Helm template processing from OasisPlatform Kubernetes deployment

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
TEMPLATE_DIR="$SCRIPT_DIR"
OUTPUT_DIR="$SCRIPT_DIR/generated"
USERS_FILE="$SCRIPT_DIR/users.yaml"

# Create output directory
mkdir -p "$OUTPUT_DIR"

# ============================================================================
# Parse Users YAML
# ============================================================================

echo "  -> Parsing users from users.yaml"

# Convert YAML to JSON for processing
# Try yq first, fallback to python
if command -v yq &> /dev/null; then
    USERS_DATA=$(yq eval '.users' "$USERS_FILE" -o=json)
else
    USERS_DATA=$(python3 -c "
import yaml, json
with open('$USERS_FILE') as f:
    data = yaml.safe_load(f)
    print(json.dumps(data['users']))
")
fi

if ! command -v jq &> /dev/null; then
    echo "  ERROR: jq is required but not installed"
    exit 1
fi

USER_COUNT=$(echo "$USERS_DATA" | jq '. | length')
echo "  -> Found $USER_COUNT user(s)"

if [ "$USER_COUNT" -eq 0 ]; then
    echo "  ERROR: No users defined in users.yaml"
    exit 1
fi

# ============================================================================
# Generate User Blueprint Entries
# ============================================================================

echo "  -> Generating user entries from template"

USER_TEMPLATE=$(cat "$TEMPLATE_DIR/oasis-users-blueprint.yaml.template")
USER_ENTRIES=()

# Process each user
while IFS= read -r user; do
    username=$(echo "$user" | jq -r '.username')
    password=$(echo "$user" | jq -r '.password')
    is_admin=$(echo "$user" | jq -r '.admin')

    echo "     - Processing user: $username"

    # Build groups (with proper YAML indentation)
    groups="    - !Find [authentik_core.group, [name, authentik Read-only]]"

    if [ "$is_admin" = "true" ]; then
        groups="${groups}"$'\n'"    - !Find [authentik_core.group, [name, admin]]"
    fi

    # Replace variables in template
    user_entry="$USER_TEMPLATE"
    user_entry="${user_entry//___USERNAME___/$username}"
    user_entry="${user_entry//___PASSWORD___/$password}"
    user_entry="${user_entry//___GROUPS___/$groups}"

    USER_ENTRIES+=("$user_entry")

done < <(echo "$USERS_DATA" | jq -c '.[]')

# Join user entries with newlines
USERS_YAML=$(printf '%s\n' "${USER_ENTRIES[@]}")

echo "  -> Generated ${#USER_ENTRIES[@]} user entry(ies)"

# ============================================================================
# Process Main Blueprint Template
# ============================================================================

echo "  -> Processing blueprint template"

BLUEPRINT_TEMPLATE=$(cat "$TEMPLATE_DIR/oasis-blueprint.yaml.template")

# Replace ___USERS___ placeholder
BLUEPRINT_YAML="${BLUEPRINT_TEMPLATE//___USERS___/$USERS_YAML}"

# Build redirect base URL
REDIRECT_BASE="${OASIS_PROTOCOL}://${OASIS_UI_HOSTNAME}"
echo "  -> Using redirect base: $REDIRECT_BASE"

# Replace hostname placeholders
BLUEPRINT_YAML="${BLUEPRINT_YAML//___OASIS_PROTOCOL___/$OASIS_PROTOCOL}"
BLUEPRINT_YAML="${BLUEPRINT_YAML//___OASIS_UI_HOSTNAME___/$OASIS_UI_HOSTNAME}"
BLUEPRINT_YAML="${BLUEPRINT_YAML//___REDIRECT_BASE___/$REDIRECT_BASE}"

# ============================================================================
# Write Output
# ============================================================================

OUTPUT_FILE="$OUTPUT_DIR/oasis-blueprint.yaml"
echo "$BLUEPRINT_YAML" > "$OUTPUT_FILE"

echo "  -> Blueprint configuration written to: $OUTPUT_FILE"

# ============================================================================
# Validate YAML
# ============================================================================

echo "  -> Validating generated YAML"

if command -v yq &> /dev/null; then
    if ! yq eval '.' "$OUTPUT_FILE" > /dev/null 2>&1; then
        echo "  ERROR: Generated YAML is invalid!"
        echo "  -> Check syntax errors in template or processing logic"
        exit 1
    fi
    echo "  OK Generated YAML is valid"
else
    # Fallback to python - use yaml.scan() which checks syntax only and
    # does not try to construct objects, so custom tags like !Find are ignored
    if ! python3 -c "import yaml; list(yaml.scan(open('$OUTPUT_FILE')))" 2>/dev/null; then
        echo "  ERROR: Generated YAML is invalid!"
        exit 1
    fi
    echo "  OK Generated YAML is valid"
fi

echo "  OK Authentik template processing complete!"
