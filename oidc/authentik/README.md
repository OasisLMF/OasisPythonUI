# Authentik Configuration for OasisPythonUI

This directory contains Authentik-specific configuration files for OIDC authentication.

## Files

- **users.yaml** - User definitions (edit to add/modify users)
- **oasis-blueprint.yaml.template** - Authentik blueprint template with ___VAR___ placeholders
- **oasis-users-blueprint.yaml.template** - User entry template
- **process-authentik-templates.sh** - Template processing script
- **generated/** - Runtime-generated configurations (gitignored)

## How It Works

1. **At deployment time**, `process-authentik-templates.sh` is executed
2. Script reads `users.yaml` and environment variables
3. For each user, generates a user entry from `oasis-users-blueprint.yaml.template`
4. Combines all users and injects into `oasis-blueprint.yaml.template`
5. Replaces hostname variables with actual values
6. Outputs final blueprint configuration to `generated/oasis-blueprint.yaml`
7. Authentik worker imports the blueprint on startup

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
- `___GROUPS___` - YAML array of groups based on admin flag
- `___USERS___` - YAML array of all generated user entries
- `___OASIS_PROTOCOL___` - http or https from .env
- `___OASIS_UI_HOSTNAME___` - hostname from .env
- `___REDIRECT_BASE___` - \${OASIS_PROTOCOL}://\${OASIS_UI_HOSTNAME}
