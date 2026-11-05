"""Create and run the showcase analyses for the public Scenarios app.

For each scenario model in the Scenarios UI config's `model_map` that is
registered on the platform, runs the model against its first portfolio
using the model's settings template, and tags the analysis name with the
showcase tag (e.g. `[showcase]`) so the app lists it on the Showcase page
and the prune job keeps it.

Idempotent: models that already have a showcase analysis are skipped
(use --force to add another). Runs are queued and not waited for.

Usage:
    python scripts/add_showcase_analyses.py -c scenarios/ui-config.json [--retry]
"""
import argparse
import json
import logging
from pathlib import Path

from utils import LOG_LEVEL, initialise_client, parse_initialise_args

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


def main():
    parser = argparse.ArgumentParser(description='Create and run Scenarios showcase analyses')
    parser.add_argument('-c', '--config', default='./scenarios/ui-config.json', type=Path,
                        help='Scenarios UI config (model_map and scenarios.showcase_tag)')
    parser.add_argument('-s', '--samples', default=10, type=int, help='Number of samples per run')
    parser.add_argument('--models', nargs='+', default=None, help='Only these model ids (default: all)')
    parser.add_argument('--force', action='store_true', help='Add a run even if one exists')
    parser.add_argument('-r', '--retry', action='store_true', help='Retry initialising client')
    parser.add_argument('-m', '--max-retries', default=10, type=int, help='Max number of retries')
    parser.add_argument('-i', '--retry_interval', default=10, type=int, help='Seconds between retries')
    args = vars(parser.parse_args())

    config = json.loads(args['config'].read_text())
    tag = config.get('scenarios', {}).get('showcase_tag', '[showcase]')
    model_map = config.get('model_map', {})

    client = initialise_client(*parse_initialise_args(**args))
    if client is None:
        raise SystemExit('Could not connect to the API')

    models = {m['model_id']: m for m in client.models.get().json()}
    portfolios = {p['name']: p for p in client.portfolios.get().json()}
    existing = [a for a in client.analyses.get().json() if a['name'].endswith(tag)]

    for model_id, portfolio_names in model_map.items():
        if args['models'] and model_id not in args['models']:
            continue
        model = models.get(model_id)
        portfolio = next((portfolios[n] for n in portfolio_names if n in portfolios), None)
        if model is None or portfolio is None:
            logger.info(f'Skipping {model_id}: model or portfolio not on the platform')
            continue
        if not args['force'] and any(a['model'] == model['id'] for a in existing):
            logger.info(f'Skipping {model_id}: showcase analysis already exists')
            continue

        template = settings_template(client, model)
        if template is None:
            logger.warning(f'Skipping {model_id}: no settings template (run add_settings_template.py first)')
            continue

        name = model_settings(client, model).get('name') or model_id
        analysis = client.create_analysis(portfolio_id=portfolio['id'], model_id=model['id'],
                                          analysis_name=f"{name} – {portfolio['name']} {tag}")
        client.upload_settings(analysis['id'], showcase_settings(template, model, args['samples']))
        client.analyses.generate_and_run(analysis['id'])
        logger.info(f"Started showcase run {analysis['id']} for {model_id} on {portfolio['name']}")


if __name__ == '__main__':
    main()
