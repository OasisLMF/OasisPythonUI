# Keycloak Configuration for OasisPythonUI

This directory contains Keycloak-specific configuration files for OIDC authentication.

## Files

- **users.yaml** - User definitions (edit to add/modify users)
- **oasis-realm.json.template** - Keycloak realm template with ___VAR___ placeholders
- **oasis-realm-user.json.template** - User entry template
- **process-keycloak-templates.sh** - Template processing script
- **generated/** - Runtime-generated configurations (gitignored)

## How It Works

1. **At deployment time**, `process-keycloak-templates.sh` is executed
2. Script reads `users.yaml` and environment variables
3. For each user, generates a user entry from `oasis-realm-user.json.template`
4. Combines all users and injects into `oasis-realm.json.template`
5. Replaces hostname variables with actual values
6. Outputs final realm configuration to `generated/oasis-realm.json`
7. Keycloak imports the generated realm on startup

## Adding Users

Edit `users.yaml`:

```yaml
users:
  - username: analyst
    password: analyst123
    admin: false
```

Then redeploy:

```bash
./install.sh
```

## Template Variables

Variables replaced by the processing script:

- `___USERNAME___` - username from users.yaml
- `___PASSWORD___` - password from users.yaml
- `___UUID___` - generated UUID
- `___ROLES___` - "default-roles-oasis"
- `___GROUPS___` - "admin" if user.admin=true, else empty
- `___USERS___` - array of all generated user entries
- `___OASIS_PROTOCOL___` - http or https from .env
- `___OASIS_UI_HOSTNAME___` - hostname from .env
- `___REDIRECT_BASE___` - \${OASIS_PROTOCOL}://\${OASIS_UI_HOSTNAME}
