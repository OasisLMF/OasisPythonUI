#!/usr/bin/env python3
"""Register an Oasis model via REST API.

Mirrors kubernetes/charts/oasis-models/resources/model_registration.sh
for Docker Compose deployments. Run as a one-shot service before the
model worker starts so that run_register_worker_v2 finds the model
already registered and skips the Django admin user lookup.

Required environment variables:
    OASIS_API_URL                    Base API URL e.g. http://server:8000
    OASIS_MODEL_SUPPLIER_ID          Model supplier ID
    OASIS_MODEL_ID                   Model ID
    OASIS_MODEL_VERSION_ID           Model version ID
    OASIS_RUN_MODE                   Run mode (v1 or v2)
    OASIS_MODEL_DATA_DIRECTORY       Directory containing model_settings.json
    OASIS_SERVICE_USERNAME_OR_ID     client_id (OIDC) or username (simple)
    OASIS_SERVICE_PASSWORD_OR_SECRET client_secret (OIDC) or password (simple)
    OASIS_USE_OIDC                   "true" for OIDC, empty/unset for simple JWT
"""

import json
import os
import time

import requests

API_URL = os.environ["OASIS_API_URL"]
SUPPLIER = os.environ["OASIS_MODEL_SUPPLIER_ID"]
MODEL = os.environ["OASIS_MODEL_ID"]
VERSION = os.environ["OASIS_MODEL_VERSION_ID"]
RUN_MODE = os.environ["OASIS_RUN_MODE"]
MODEL_DATA_DIR = os.environ["OASIS_MODEL_DATA_DIRECTORY"]
SVC_ID = os.environ["OASIS_SERVICE_USERNAME_OR_ID"]
SVC_SECRET = os.environ["OASIS_SERVICE_PASSWORD_OR_SECRET"]
USE_OIDC = os.environ.get("OASIS_USE_OIDC", "").lower() == "true"

settings_file = os.path.join(MODEL_DATA_DIR, "model_settings.json")

print("\n=== Register model ===")
print(f"  API URL    : {API_URL}")
print(f"  Supplier   : {SUPPLIER}")
print(f"  Model      : {MODEL}")
print(f"  Version    : {VERSION}")
print(f"  Run mode   : {RUN_MODE}")

# Authenticate
if USE_OIDC:
    print("  Auth       : OIDC client credentials")
    auth_data = {"client_id": SVC_ID, "client_secret": SVC_SECRET}
else:
    print("  Auth       : simple JWT")
    auth_data = {"username": SVC_ID, "password": SVC_SECRET}

for attempt in range(1, 13):
    resp = requests.post(f"{API_URL}/access_token/", json=auth_data)
    if resp.ok:
        break
    if attempt < 12:
        print(f"  Auth failed ({resp.status_code}), retrying in 10s... ({attempt}/12)")
        time.sleep(10)
else:
    resp.raise_for_status()
token = resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("  Authenticated successfully")

# Check if model already exists
existing = requests.get(
    f"{API_URL}/v2/models/",
    params={"supplier_id": SUPPLIER, "version_id": VERSION},
    headers=headers,
).json()

match = next(
    (m for m in existing
     if m["supplier_id"].lower() == SUPPLIER.lower()
     and m["model_id"].lower() == MODEL.lower()
     and m["version_id"].lower() == VERSION.lower()),
    None,
)

if match:
    model_id = match["id"]
    print(f"  Model already registered (id={model_id})")
else:
    print("  Model not found — registering")
    resp = requests.post(
        f"{API_URL}/v2/models/",
        json={
            "supplier_id": SUPPLIER,
            "model_id": MODEL,
            "version_id": VERSION,
            "run_mode": RUN_MODE.upper(),
        },
        headers=headers,
    )
    resp.raise_for_status()
    model_id = resp.json()["id"]
    print(f"  Created model (id={model_id})")

# Upload model settings
if os.path.exists(settings_file):
    print("  Uploading model settings")
    with open(settings_file) as f:
        settings = json.load(f)
    resp = requests.post(
        f"{API_URL}/v2/models/{model_id}/settings/",
        json=settings,
        headers=headers,
    )
    resp.raise_for_status()
    print("  Model settings uploaded")
else:
    print(f"  WARNING: {settings_file} not found, skipping settings upload")

print("  Done\n")
