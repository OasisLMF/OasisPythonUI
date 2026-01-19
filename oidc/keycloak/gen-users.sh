#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
TPL_DIR="$ROOT_DIR"
OUT_DIR="$ROOT_DIR/rendered"

USERS_FILE="$ROOT_DIR/users.yaml"
USER_TPL="$TPL_DIR/oasis-realm-user.json"
REALM_TPL="$TPL_DIR/oasis-realm.json"
OUT_REALM="$OUT_DIR/oasis-realm.json"

mkdir -p "$OUT_DIR"

echo "Rendering Keycloak realm..."

USER_JSONS=()

user_count=$(yq '.users | length' "$USERS_FILE")

for i in $(seq 0 $((user_count - 1))); do
  username=$(yq -r ".users[$i].username" "$USERS_FILE")
  password=$(yq -r ".users[$i].password" "$USERS_FILE")
  admin=$(yq -r ".users[$i].admin" "$USERS_FILE")

  uuid=$(uuidgen)

  groups=""
  if [[ "$admin" == "true" ]]; then
    groups='"admin"'
  fi

  echo "Generating user: $username"
  rendered_user=$(sed \
    -e "s/___UUID___/$uuid/g" \
    -e "s/___USERNAME___/$username/g" \
    -e "s/___PASSWORD___/$password/g" \
    -e 's/___ROLES___/"default-roles-oasis"/g' \
    -e "s/___GROUPS___/$groups/g" \
    "$USER_TPL")

  USER_JSONS+=("$rendered_user")
done

users_combined=$(printf ",\n%s" "${USER_JSONS[@]}")
users_combined="${users_combined:2}"

perl -0777 -pe "s/\"___USERS___\"/$users_combined/s" "$REALM_TPL" > "$OUT_REALM"

echo "Realm rendered at $OUT_REALM"