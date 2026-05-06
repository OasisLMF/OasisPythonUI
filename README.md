<img src="https://oasislmf.org/packages/oasis_theme_package/themes/oasis_theme/assets/src/oasis-lmf-colour.png" alt="Oasis LMF logo" width="250"/>

# Oasis Python UI

A web-based UI utilising [Streamlit](https://github.com/streamlit/streamlit) to
manage exposure data and run modeling workflows on the OasisLMF platform.

The current version of the UI contains the following pages:

- `/analyses` - View and create portfolios and analyses.
- `/dashboard` - View the output of completed analyses.
- `/simplified` - Simplified UI which allows for the running of analyses using previously loaded portfolios & models.

## Prerequisites

- `git`
- `docker` with Compose v2 (`docker compose`)

## Quick Start

### 1. Choose an authentication type

Three modes are supported. Copy the matching environment template:

```bash
cp .env.simple .env      # No OIDC — username/password login
cp .env.keycloak .env    # Keycloak OIDC
cp .env.authentik .env   # Authentik OIDC
```

Edit `.env` to adjust the hostname, passwords, or image versions if needed.

### 2. Configure `.streamlit/secrets.toml`

This file tells the UI how to authenticate against the Oasis API backend.
Edit `.streamlit/secrets.toml` before running the installer — it is mounted
read-only into the UI container.

**Simple auth:**
```toml
auth_type = 'simple'
user = 'admin'
password = 'password'
```

**Keycloak or Authentik OIDC:**
```toml
auth_type = 'oidc'
client_id = 'oasis-service'
client_secret = 'serviceNotSoSecret'
```

### 3. Add the hostname to `/etc/hosts`

The default hostname is `ui.oasis.local`. Add it to your hosts file so your
browser can resolve it:

```bash
echo "127.0.0.1  ui.oasis.local" | sudo tee -a /etc/hosts
```

### 4. Run the installer

```bash
./install.sh
```

The installer clones the PiWind demo model, processes OIDC templates (if
applicable), builds the UI image, and starts all services. It will prompt
before redeploying if a previous installation is detected.

To tear everything down (removes containers and volumes):

```bash
./install.sh --uninstall
```

## Access Points

All services are reachable on port 80 via Traefik after a successful install:

| Service | URL |
|---------|-----|
| UI | `http://ui.oasis.local/` |
| API | `http://ui.oasis.local/api/` |
| Keycloak Admin | `http://ui.oasis.local/auth/` |
| Authentik Admin | `http://ui.oasis.local/authentik/` |

## Switching Between Auth Types

1. Bring down the current stack:
   ```bash
   ./install --uninstall
   ```
2. Copy the new `.env` template and edit if needed:
   ```bash
   cp .env.keycloak .env
   ```
3. Update `.streamlit/secrets.toml` to match if required (see step 2 of Quick Start).
4. Re-run the installer:
   ```bash
   ./install.sh
   ```

## Docker Compose Architecture

The stack is assembled from multiple Compose files depending on auth type:

```
Always loaded:
  docker-compose.yml         # Core platform: server, worker, databases, broker
  docker-compose.ui.yml      # Streamlit UI + Traefik reverse proxy

Conditionally loaded:
  docker-compose.keycloak.yml    # Keycloak + its PostgreSQL DB  (API_AUTH_TYPE=keycloak)
  docker-compose.authentik.yml   # Authentik + its PostgreSQL DB  (API_AUTH_TYPE=authentik)
```

`install.sh` builds the correct `docker compose -f ... up` command automatically.

## Key Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `API_AUTH_TYPE` | Auth mode: `simple`, `keycloak`, or `authentik` | `authentik` |
| `OASIS_UI_HOSTNAME` | Hostname the UI and proxy listen on | `ui.oasis.local` |
| `OASIS_PROTOCOL` | `http` or `https` | `http` |
| `VERS_API` | Oasis server image tag | `2.5` |
| `VERS_WORKER` | Oasis worker image tag | `2.5` |
| `VERS_UI` | Python UI image tag | `latest` |

See the `.env.*` templates for the full list with inline comments.

## Adding Users

### Simple auth

The default admin user (`admin` / `password`) is created automatically.
Additional users must be added via the Oasis API or admin interface.

### Keycloak

Edit `oidc/keycloak/users.yaml` and re-run `./install.sh`, or add users
through the Keycloak admin console at `/auth/` (`keycloak` / `password`).

### Authentik

Edit `oidc/authentik/users.yaml` and re-run `./install.sh`, or add users
through the Authentik admin console at `/authentik/` (`akadmin` / `password`).

## Troubleshooting

Usually first thing to try before anything is clearing browser cache/cookies for the hostname.

**OIDC login redirects to the wrong URL**
- Confirm `OASIS_UI_HOSTNAME` in `.env` matches the hostname you use in the browser.
- Confirm the same hostname resolves locally (check `/etc/hosts`).

**UI cannot reach the API**
- Verify Traefik is running: `docker compose ps traefik`.
- Check that the server container is healthy: `docker compose ps server`.
- Inspect Traefik routing logs: `docker compose logs traefik`.

**Keycloak / Authentik container unhealthy**
- Check logs: `docker compose logs keycloak` or `docker compose logs authentik-server`.
- The IdP database container must be healthy first: `docker compose ps`.
- First startup can take 2–3 minutes while blueprints and realms are imported.

**Logs and status**
```bash
docker compose ps                          # service health
docker compose logs -f <container_name>    # UI logs
```

## Security Notes

- The `.env` templates and `users.yaml` files ship with **demo credentials**.
  Change all passwords before any non-local deployment.

## Public Demo

The public site is at https://ui.oasislmf-scenarios.com/
Default scenarios in the tool are processed/hosted at https://github.com/OasisLMF/Scenarios
