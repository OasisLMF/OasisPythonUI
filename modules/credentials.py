"""Credentials for the UI's service account.

Environment variables set by install.sh take precedence over
`.streamlit/secrets.toml`, so a deployment's credentials only need setting in
`.env`:

- `API_AUTH_TYPE`: `simple`, or an OIDC provider (`keycloak`, `authentik`)
- `OASIS_SERVICE_USERNAME_OR_ID`: username (simple) or client id (OIDC)
- `OASIS_SERVICE_PASSWORD_OR_SECRET`: password (simple) or client secret (OIDC)
"""
import os

import streamlit as st


def _secret(key, default=None):
    try:
        return st.secrets.get(key, default)
    except Exception:  # noqa: BLE001 - no secrets file is fine when env vars are set
        return default


def service_auth_type():
    """'simple' or 'oidc'."""
    auth = os.environ.get('API_AUTH_TYPE') or _secret('auth_type', 'simple')
    return 'simple' if auth == 'simple' else 'oidc'


def service_credentials():
    """`(auth_type, id, secret)` for the service account."""
    auth = service_auth_type()
    env_id = os.environ.get('OASIS_SERVICE_USERNAME_OR_ID')
    env_secret = os.environ.get('OASIS_SERVICE_PASSWORD_OR_SECRET')
    if env_id and env_secret:
        return auth, env_id, env_secret
    if auth == 'simple':
        return auth, _secret('user', 'admin'), _secret('password', 'password')
    return auth, _secret('client_id', 'oasis-service'), _secret('client_secret', 'serviceNotSoSecret')


def service_client_kwargs():
    """Keyword arguments for `ClientInterface` / `APIClient` using the service account."""
    auth, ident, secret = service_credentials()
    if auth == 'simple':
        return {'auth_type': 'simple', 'username': ident, 'password': secret}
    return {'auth_type': 'oidc', 'client_id': ident, 'client_secret': secret}
