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

The installer stages the model data for the selected model set, processes OIDC
templates (if applicable), pulls the images, and starts all services. It will
prompt before redeploying if a previous installation is detected.

| Option | Description |
|--------|-------------|
| `-m`, `--model-set <name>` | Model set to deploy. Defaults to `MODEL_SET` from `.env`, or `piwind`. |
| `--build-ui` | Build the UI image locally instead of pulling `PYTHONUI_IMG:VERS_UI`. |
| `-u`, `--uninstall` | Bring the stack down and delete its volumes. |
| `-h`, `--help` | Show usage. |

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

`install.sh` layers several Compose files into a single `docker compose`
command. The model workers live in a file of their own, so the core platform,
the UI and the auth stack stay model-agnostic:

```
Always loaded:
  docker-compose.yml                     # Core platform: Traefik, server, websocket, databases, broker, filestore
  docker-compose.models.<model-set>.yml  # Model workers and model registration for one model set
  docker-compose.ui.yml                  # Streamlit UI

Conditionally loaded:
  docker-compose.keycloak.yml    # Keycloak + its PostgreSQL DB   (API_AUTH_TYPE=keycloak)
  docker-compose.authentik.yml   # Authentik + its PostgreSQL DB  (API_AUTH_TYPE=authentik)
```

### Model sets — `docker-compose.models.<model-set>.yml`

`docker-compose.yml` defines no model workers at all. Everything
model-specific is confined to a `docker-compose.models.<model-set>.yml` file:

- one worker service per model, carrying its `OASIS_MODEL_SUPPLIER_ID`,
  `OASIS_MODEL_ID`, `OASIS_MODEL_VERSION_ID` and `OASIS_RUN_MODE`
- the volume mount that supplies that model's data
- any `model-registration` job needed to register the models with the API

Exactly one model set is loaded per deployment. Pick it with `-m/--model-set`,
or set `MODEL_SET` in `.env` so a bare `./install.sh` deploys it:

```bash
./install.sh -m piwind      # default: the PiWind demo model
./install.sh -m scenarios   # PiWind plus the public scenario models
```

Model sets shipped in this repository:

| File | Contents |
|------|----------|
| `docker-compose.models.piwind.yml` | A `model-registration` one-shot and `piwind-worker`, with model data from `./OasisPiWind/`. |
| `docker-compose.models.scenarios.yml` | `piwind-worker` plus the scenario workers (Impact Forecasting, JBA, ARA, IPE), with model data from `${SCENARIOS_PATH}`. |

Because the split is by filename, adding a model set means dropping two new
files into the root directory — no edits to `docker-compose.yml`, `install.sh`
or the auth files:

1. Write `docker-compose.models.<name>.yml` with the worker services. The
   workers join the core stack, so they can depend on `server`, `celery-db` and
   `broker` and mount the shared `filestore-data` volume directly.
2. Optionally add `get-<name>.sh` to fetch the model data (see below).
3. Deploy with `./install.sh -m <name>`.

`install.sh --uninstall` passes *every* `docker-compose.models.*.yml` to
`docker compose down`, so the model workers are torn down whichever set was
deployed.

#### Model data — `get-<model-set>.sh`

The Compose file describes how a model runs; the matching `get-<model-set>.sh`
puts its data on disk. Before bringing the stack up, `install.sh` runs
`get-$MODEL_SET.sh` if it exists, and otherwise assumes the data is already in
place.

| Script | What it does |
|--------|--------------|
| `get-piwind.sh` | Clones `OasisLMF/OasisPiWind` at `VERS_PIWIND` into `./OasisPiWind/`. No-ops once cloned. |
| `get-scenarios.sh` | Runs `get-piwind.sh`, clones `OasisLMF/Scenarios` into `$SCENARIOS_PATH`, then runs that repository's `get_s3_data_reduced.sh` to download the model files. Each step is skipped if it has already been done. |

The scripts are idempotent and safe to run on their own, which is the easy way
to pre-stage model data on a server before deploying, or to refresh it without
a redeploy:

```bash
SCENARIOS_PATH=/home/ubuntu/Scenarios ./get-scenarios.sh
```

When writing your own, keep it re-runnable: `install.sh` calls it on every
deploy, including redeploys over an existing installation.

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

### Deployment overrides

These variables decide *what* gets deployed and *what the UI shows*, rather
than how the platform is wired together. They are read straight from `.env` by
`install.sh` and the Compose files, and each falls back to the layout in this
repository — so a plain checkout still deploys unchanged with none of them set.
They are not in the `.env.*` templates; add the ones a deployment needs.

| Variable | Default | Purpose |
|----------|---------|---------|
| `MODEL_SET` | `piwind` | Which `docker-compose.models.<name>.yml` / `get-<name>.sh` pair to deploy. `-m/--model-set` overrides it for one run. |
| `SCENARIOS_PATH` | *(unset)* | Host directory holding the scenario model data. Required by the `scenarios` model set — both `get-scenarios.sh` and the worker mounts read it. |
| `UI_CONFIG` | `./ui-config.json` | The UI's config file: pages, post-login page, model-to-exposure map, footer, and `skip_login`. |
| `UI_DEFAULTS` | `./defaults/` | Per-model default analysis settings the UI pre-fills when creating an analysis. |
| `UI_ASSETS` | `./ui_assets/` | Files `UI_CONFIG` refers to as `ui_assets/<file>` — footer text, logos, anything a deployment supplies. |
| `UI_STREAMLIT` | `./.streamlit/` | The Streamlit directory mounted read-only: `secrets.toml` and `config.toml`. |
| `PYTHONUI_IMG` / `VERS_UI` | `coreoasis/oasispythonui_app` / `latest` | UI image pulled at deploy time, and the tag `make build` / `make push` produce. |


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

**`install.sh` exits with `no model set '<name>'`**
- The model set has no `docker-compose.models.<name>.yml` in the root directory.
  Check the spelling of `-m/--model-set` or `MODEL_SET`.

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
