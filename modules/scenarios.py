"""Shared logic for the public Scenarios app (`scenarios_app.py`).

The Scenarios app is credential free: every visitor uses the same service
account, so analyses are attributed to a visitor by a tag in the analysis
name. Visitors see their own runs plus a curated set of showcase runs
(tagged `[showcase]`), and runs are limited by the `scenarios` section of the
UI config.
"""
import re
import uuid
from dataclasses import dataclass

import streamlit as st

from modules.oed import country_name, peril_family
from modules.status import IN_PROGRESS_STATUSES, is_active  # noqa: F401 - re-exported

VISITOR_PARAM = 'v'
_VISITOR_KEY = 'scenarios_visitor_id'
_TAG_PATTERN = re.compile(r'\s*\[(showcase|v:[0-9a-f]+)\]\s*$')

IN_PROGRESS = IN_PROGRESS_STATUSES

# Group-by choices offered to visitors, as (label, OED field)
GROUP_BY_OPTIONS = [('Portfolio', 'PortNumber'), ('Country', 'CountryCode'), ('Location', 'LocNumber')]


@dataclass
class ScenarioLimits:
    """Run limits for the public Scenarios app (`scenarios` in the UI config)."""

    max_samples: int = 50
    default_samples: int = 10
    max_active_runs_per_visitor: int = 2
    max_active_runs: int = 3
    processes_per_run: int = 2
    showcase_tag: str = '[showcase]'

    @classmethod
    def from_config(cls, ui_config):
        settings = getattr(ui_config, 'scenarios', {}) or {}
        known = {k: v for k, v in settings.items() if k in cls.__dataclass_fields__}
        limits = cls(**known)
        limits.default_samples = min(limits.default_samples, limits.max_samples)
        return limits


def limit_processes(settings, processes):
    """Cap the model processes a run uses (oasislmf computation settings).

    oasislmf defaults to one process per CPU for both the lookup and the loss
    calculation, so several concurrent runs on one host can exhaust its memory.
    Values already set in the settings (e.g. by the template) are kept.
    """
    if processes and processes > 0:
        computation = settings.setdefault('computation_settings', {})
        computation.setdefault('kernel_num_processes', processes)
        computation.setdefault('lookup_num_processes', processes)
    return settings


def visitor_id():
    """This visitor's id, kept in the URL (`?v=...`) so it survives reloads.

    Page navigation clears query parameters, so the id is also kept in the
    session and written back to the URL on every page.
    """
    vid = st.query_params.get(VISITOR_PARAM) or st.session_state.get(_VISITOR_KEY)
    if not vid or not re.fullmatch(r'[0-9a-f]{12}', str(vid)):
        vid = uuid.uuid4().hex[:12]
    st.session_state[_VISITOR_KEY] = vid
    if st.query_params.get(VISITOR_PARAM) != vid:
        st.query_params[VISITOR_PARAM] = vid
    return vid


def visitor_tag(vid):
    return f'[v:{vid}]'


def tagged_name(name, tag):
    return f'{name} {tag}'


def display_name(name):
    """Analysis name without its visitor/showcase tag."""
    return _TAG_PATTERN.sub('', name or '')


def is_showcase(analysis, limits):
    return (analysis.get('name') or '').endswith(limits.showcase_tag)


def visitor_analyses(analyses, vid):
    tag = visitor_tag(vid)
    return [a for a in analyses if (a.get('name') or '').endswith(tag)]


def showcase_analyses(analyses, limits, models=None, ui_config=None):
    """Showcase runs, limited to configured scenario models when `models` and `ui_config` are given.

    Runs left over from scenarios since removed from the config are then not shown.
    """
    runs = [a for a in analyses if is_showcase(a, limits)]
    if models is not None and ui_config is not None:
        configured = {m['id'] for m in models if m.get('model_id') in (ui_config.model_map or {})}
        runs = [a for a in runs if a.get('model') in configured]
    return runs


def run_blocked_reason(analyses, vid, limits):
    """Why a new run can't start right now (None if it can)."""
    active = [a for a in analyses if is_active(a)]
    mine = [a for a in visitor_analyses(active, vid)]
    if len(mine) >= limits.max_active_runs_per_visitor:
        return (f'You already have {len(mine)} run(s) in progress. '
                'Wait for one to finish before starting another.')
    if len(active) >= limits.max_active_runs:
        return 'The service is busy running other analyses. Please try again in a few minutes.'
    return None


def scenario_portfolios(model, portfolios, ui_config):
    """Portfolios offered for a scenario model (from the config's `model_map`)."""
    names = (ui_config.model_map or {}).get(model.get('model_id'))
    if names is None:
        return []
    by_name = {p['name']: p for p in portfolios}
    return [by_name[n] for n in names if n in by_name]


def scenario_models(models, portfolios, ui_config):
    """Models that have at least one configured portfolio available."""
    return [m for m in models if scenario_portfolios(m, portfolios, ui_config)]


def _column(df, name):
    """Column `name` of an OED DataFrame, matched case-insensitively (or None)."""
    match = next((c for c in df.columns if c.lower() == name.lower()), None)
    return df[match] if match is not None else None


def vulnerability_info(model_settings):
    """The vulnerability functions a scenario uses, from its model settings.

    Scenarios describe them in `data_settings.vulnerability`: `source`, `description`
    and optionally `url`. Returns None when a scenario doesn't.
    """
    info = ((model_settings or {}).get('data_settings') or {}).get('vulnerability')
    if not isinstance(info, dict) or not info.get('source'):
        return None
    return {key: info[key] for key in ('source', 'description', 'url') if info.get(key)}


def scenario_catalogue(models, portfolios, ui_config, settings_for, locations_for=None):
    """Scenarios to browse, with title, peril, countries, provider and description.

    The title and description come from the model's settings; the peril and
    countries from the scenario's first portfolio (`locations_for(portfolio)`
    returns its location DataFrame), using OED peril and country names.

    Args:
        models: model records from the API.
        portfolios: portfolio records from the API.
        ui_config: UI config with `model_map`.
        settings_for: callable returning a model's settings (for name and description).
        locations_for: optional callable returning a portfolio's location DataFrame.
    """
    catalogue = []
    for model in scenario_models(models, portfolios, ui_config):
        settings = settings_for(model) or {}
        countries, peril = None, None
        if locations_for is not None:
            locations = locations_for(scenario_portfolios(model, portfolios, ui_config)[0])
            if locations is not None:
                codes = _column(locations, 'CountryCode')
                if codes is not None:
                    countries = sorted(codes.dropna().astype(str).unique())
                covered = _column(locations, 'LocPerilsCovered')
                if covered is not None:
                    perils = {c for value in covered.dropna().astype(str).unique() for c in value.split(';')}
                    peril = ', '.join(sorted({peril_family(c) for c in perils if c}))

        catalogue.append({
            'id': model['id'],
            'title': settings.get('name') or model['model_id'],
            'peril': peril or 'Not specified',
            'countries': [country_name(c) for c in countries or []],
            'provider': model.get('supplier_id') or '',
            'description': settings.get('description') or '',
            'vulnerability': vulnerability_info(settings),
        })
    return sorted(catalogue, key=lambda e: e['title'].lower())
