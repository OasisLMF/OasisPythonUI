"""Create and run the showcase analyses for the public Scenarios app.

For each scenario model in the Scenarios UI config's `model_map` that is
registered on the platform, runs the model against its first portfolio
using the model's settings template, and tags the analysis name with the
showcase tag (e.g. `[showcase]`) so the app lists it on the Showcase page
and the prune job keeps it.

Runs one scenario at a time (--max-concurrent), waiting for each to finish,
and caps each run's processes (scenarios.processes_per_run): starting every
scenario at once can exhaust the host's memory.

Idempotent: scenarios with a completed or in-progress showcase run are
skipped; failed or cancelled showcase runs are replaced.

Usage:
    python scripts/add_showcase_analyses.py -c scenarios/ui-config.json [--retry]
"""
import argparse
import json
import logging
import time
from pathlib import Path

from utils import LOG_LEVEL, initialise_client, parse_initialise_args

from modules.scenarios import is_active, limit_processes

FAILED = ['INPUTS_GENERATION_ERROR', 'INPUTS_GENERATION_CANCELLED', 'RUN_ERROR', 'RUN_CANCELLED']
# A generate-and-run passes through READY between input generation and the
# loss run, so only these statuses mean a showcase run has finished
FINISHED = ['RUN_COMPLETED'] + FAILED

logger = logging.getLogger(__name__)
logging.basicConfig(level=LOG_LEVEL)


def model_settings(client, model):
    try:
        return client.models.settings.get(model['id']).json() or {}
    except Exception:  # noqa: BLE001 - a model without settings still gets a showcase run
        return {}


def settings_template(client, model):
    templates = client.models.setting_templates.get(model['id']).json() or []
    if not templates:
        return None
    latest = max(t['id'] for t in templates)
    return client.models.setting_templates.content.get(model['id'], latest).json()


def showcase_settings(template, model, samples):
    settings = dict(template)
    settings['model_supplier_id'] = model['supplier_id']
    settings['model_name_id'] = model['model_id']
    settings['number_of_samples'] = samples
    settings.setdefault('join_summary_info', True)
    return settings


def wait_for_slot(client, running, max_concurrent, timeout):
    """Block until fewer than `max_concurrent` of `running` are in progress."""
    start = time.time()
    while True:
        statuses = {i: client.analyses.get(i).json()['status'] for i in running}
        for i, status in statuses.items():
            if status in FINISHED:
                logger.info(f'Showcase run {i} finished: {status}')
                running.remove(i)
        if len(running) < max_concurrent:
            return
        if time.time() - start > timeout:
            raise SystemExit(f'Timed out waiting for showcase runs {running}')
        time.sleep(15)


def main():
    parser = argparse.ArgumentParser(description='Create and run Scenarios showcase analyses')
    parser.add_argument('-c', '--config', default='./scenarios/ui-config.json', type=Path,
                        help='Scenarios UI config (model_map and scenarios.showcase_tag)')
    parser.add_argument('-s', '--samples', default=10, type=int, help='Number of samples per run')
    parser.add_argument('--models', nargs='+', default=None, help='Only these model ids (default: all)')
    parser.add_argument('--force', action='store_true', help='Add a run even if one exists')
    parser.add_argument('--max-concurrent', default=1, type=int,
                        help='Showcase runs in progress at once (default 1)')
    parser.add_argument('--timeout', default=3600, type=int, help='Seconds to wait for a run to finish')
    parser.add_argument('-r', '--retry', action='store_true', help='Retry initialising client')
    parser.add_argument('-m', '--max-retries', default=10, type=int, help='Max number of retries')
    parser.add_argument('-i', '--retry_interval', default=10, type=int, help='Seconds between retries')
    args = vars(parser.parse_args())

    config = json.loads(args['config'].read_text())
    tag = config.get('scenarios', {}).get('showcase_tag', '[showcase]')
    processes = config.get('scenarios', {}).get('processes_per_run', 2)
    model_map = config.get('model_map', {})

    client = initialise_client(*parse_initialise_args(**args))
    if client is None:
        raise SystemExit('Could not connect to the API')

    models = {m['model_id']: m for m in client.models.get().json()}
    portfolios = {p['name']: p for p in client.portfolios.get().json()}
    existing = [a for a in client.analyses.get().json() if a['name'].endswith(tag)]
    running = [a['id'] for a in existing if is_active(a)]

    for model_id, portfolio_names in model_map.items():
        if args['models'] and model_id not in args['models']:
            continue
        model = models.get(model_id)
        portfolio = next((portfolios[n] for n in portfolio_names if n in portfolios), None)
        if model is None or portfolio is None:
            logger.info(f'Skipping {model_id}: model or portfolio not on the platform')
            continue
        mine = [a for a in existing if a['model'] == model['id']]
        if not args['force'] and any(a['status'] not in FAILED for a in mine):
            logger.info(f'Skipping {model_id}: showcase analysis already exists')
            continue
        for failed in [a for a in mine if a['status'] in FAILED]:
            logger.info(f"Replacing failed showcase run {failed['id']} ({failed['status']}) for {model_id}")
            client.analyses.delete(failed['id'])

        template = settings_template(client, model)
        if template is None:
            logger.warning(f'Skipping {model_id}: no settings template (run add_settings_template.py first)')
            continue

        wait_for_slot(client, running, args['max_concurrent'], args['timeout'])
        name = model_settings(client, model).get('name') or model_id
        analysis = client.create_analysis(portfolio_id=portfolio['id'], model_id=model['id'],
                                          analysis_name=f"{name} – {portfolio['name']} {tag}")
        settings = limit_processes(showcase_settings(template, model, args['samples']), processes)
        client.upload_settings(analysis['id'], settings)
        client.analyses.generate_and_run(analysis['id'])
        running.append(analysis['id'])
        logger.info(f"Started showcase run {analysis['id']} for {model_id} on {portfolio['name']}")

    # Wait for the last runs so setup only finishes when the showcase is ready
    wait_for_slot(client, running, 1, args['timeout'])
    logger.info('Showcase runs complete')


if __name__ == '__main__':
    main()
