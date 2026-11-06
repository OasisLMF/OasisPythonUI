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

VISITOR_PARAM = 'v'
_VISITOR_KEY = 'scenarios_visitor_id'
_TAG_PATTERN = re.compile(r'\s*\[(showcase|v:[0-9a-f]+)\]\s*$')

IN_PROGRESS = ['INPUTS_GENERATION_QUEUED', 'INPUTS_GENERATION_STARTED', 'RUN_QUEUED', 'RUN_STARTED']

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


def showcase_analyses(analyses, limits):
    return [a for a in analyses if is_showcase(a, limits)]


def run_blocked_reason(analyses, vid, limits):
    """Why a new run can't start right now (None if it can)."""
    active = [a for a in analyses if a.get('status') in IN_PROGRESS]
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
