#!/bin/bash
# Load the Scenarios app's data onto the platform: exposure portfolios,
# analysis settings templates and showcase analyses.
#
# Runs as the one-shot `scenarios-setup` service (docker-compose.models.scenarios.yml)
# from the UI image, with /usr/src/app as the working directory. Every step is
# idempotent, so it is safe to run on every deploy.
set -e

CONFIG=${SCENARIOS_UI_CONFIG:-scenarios/ui-config.json}
MIN_MODELS=${SCENARIOS_MIN_MODELS:-1}

echo "=== Waiting for $MIN_MODELS scenario models to register ==="
# Workers register their models as they start. Wait for all of them, but carry
# on with whatever has registered if some never do (their scenarios are skipped).
python3 - "$MIN_MODELS" <<'PY'
import sys, time
sys.path.insert(0, 'scripts')
from utils import initialise_client
client = initialise_client(max_retries=30, retry_interval=10)
if client is None:
    sys.exit('Could not connect to the API')
expected = int(sys.argv[1])
for _ in range(60):
    models = sorted(m['model_id'] for m in client.models.get().json())
    if len(models) >= expected:
        break
    time.sleep(10)
print(f'{len(models)} of {expected} models registered: {", ".join(models)}')
if len(models) < expected:
    print('WARNING: not all models registered; scenarios without a model are skipped')
PY

echo "=== Adding exposure portfolios ==="
python3 scripts/add_test_portfolios.py -c scenarios/portfolios.json -r

echo "=== Adding analysis settings templates ==="
python3 scripts/add_settings_template.py -c scenarios/a_settings.json -r

echo "=== Starting showcase analyses ==="
python3 scripts/add_showcase_analyses.py -c "$CONFIG" -r

echo "=== Scenarios setup complete ==="
