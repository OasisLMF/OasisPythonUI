"""Helpers shared by the Scenarios app pages."""
import json
import logging
from copy import deepcopy
from pathlib import Path

import streamlit as st
from oasis_data_manager.errors import OasisException
from requests.exceptions import HTTPError

from modules.config import retrieve_ui_config
from modules.scenarios import GROUP_BY_OPTIONS, ScenarioLimits, display_name, is_showcase, visitor_id, vulnerability_info
from modules.schemas import PERSPECTIVES
from modules.settings import get_analyses_settings
from pages.components.common import format_status
from pages.components.data import analysis_files, analysis_settings, cached_model_settings
from pages.components.results import render_results
from pages.components.settings_editor import default_settings

logger = logging.getLogger(__name__)


class Context:
    """Per-run page context: API client, config, limits and visitor id."""

    def __init__(self):
        self.ci = st.session_state['client_interface']
        self.ui_config = retrieve_ui_config()
        self.limits = ScenarioLimits.from_config(self.ui_config)
        self.vid = visitor_id()

    def scenario_name(self, model):
        return cached_model_settings(self.ci, model).get('name') or model['model_id']

    def run_title(self, analysis, models_by_id):
        """How to name a run: showcase runs by their scenario's name, others by their run name.

        The scenario name comes from the model settings, so a renamed scenario doesn't need its
        showcase rebuilt.
        """
        model = models_by_id.get(analysis.get('model'))
        if model is not None and is_showcase(analysis, self.limits):
            return self.scenario_name(model)
        return display_name(analysis['name'])


def footer(ui_config):
    """Disclaimer / licence footer from the UI config, on every Scenarios page."""
    path = (ui_config.footer or {}).get('path')
    if not path:
        return
    try:
        text = Path(path).read_text()
    except OSError:
        logger.error(f'Footer file not found at {path}')
        return
    st.divider()
    st.caption(text)


def vulnerability_note(model_settings):
    """Which vulnerability functions a scenario uses (from its model settings)."""
    info = vulnerability_info(model_settings)
    if info is None:
        st.caption('**Vulnerability:** not documented for this scenario.')
        return
    source = f"[{info['source']}]({info['url']})" if info.get('url') else info['source']
    st.markdown(f'**Vulnerability:** {source}',
                help='How much damage the hazard causes to a building, as a share of its value. '
                     'See the Guide for more on vulnerability functions.')
    if info.get('description'):
        st.caption(info['description'])


def run_settings(ci, model, number_of_samples, group_fields):
    """Analysis settings for a scenario run.

    Starts from the model's latest settings template on the platform (falling
    back to a bundled defaults/ file, then model defaults) and applies the
    visitor's choices: number of samples and group-by fields. Group-by fields
    are written into the outputs (join_summary_info).
    """
    settings = None
    try:
        templates = ci.models.setting_templates.get(model['id']) or []
        if templates:
            latest = max(t['id'] for t in templates)
            settings = ci.models.setting_templates.get_contents(model['id'], latest)
    except (HTTPError, OasisException, AttributeError) as e:
        logger.warning(f"No settings template for model {model['id']}: {e}")
    if not settings:
        paths = get_analyses_settings(model_name_id=model['model_id'])
        if paths:
            settings = json.loads(Path(paths[0]).read_text())
    if not settings:
        settings = default_settings(model, cached_model_settings(ci, model))

    settings = deepcopy(settings)
    settings['model_supplier_id'] = model['supplier_id']
    settings['model_name_id'] = model['model_id']
    settings['number_of_samples'] = number_of_samples
    settings.setdefault('join_summary_info', True)
    for p in PERSPECTIVES:
        if settings.get(f'{p}_output'):
            for level in settings.get(f'{p}_summaries') or []:
                if group_fields:
                    level['oed_fields'] = list(group_fields)
                else:
                    level.pop('oed_fields', None)
    return settings


def run_summary(ctx, analysis, settings, models_by_id, portfolios_by_id):
    model = models_by_id.get(analysis['model'], {})
    portfolio = portfolios_by_id.get(analysis['portfolio'], {})
    fields = []
    for p in PERSPECTIVES:
        for level in (settings or {}).get(f'{p}_summaries') or []:
            fields = level.get('oed_fields') or fields
    labels = {field: label for label, field in GROUP_BY_OPTIONS}
    facts = [('Scenario', ctx.scenario_name(model) if model else '—'),
             ('Exposure', portfolio.get('name', '—')),
             ('Samples', (settings or {}).get('number_of_samples', '—')),
             ('Losses broken down by', ', '.join(labels.get(f, f) for f in fields) or 'Total only')]
    # Plain text rather than st.metric, which truncates long scenario names
    for col, (label, value) in zip(st.columns([3, 2, 1, 2]), facts):
        col.caption(label)
        col.markdown(f'**{value}**')


def analysis_results(ctx, analysis, models_by_id, portfolios_by_id, key):
    """Summary, results and downloads for a completed analysis."""
    st.subheader(ctx.run_title(analysis, models_by_id))
    if analysis['status'] != 'RUN_COMPLETED':
        st.info(f"{format_status(analysis['status'])}. Results appear here when the run completes.")
        return

    settings = analysis_settings(ctx.ci, analysis)
    run_summary(ctx, analysis, settings, models_by_id, portfolios_by_id)
    if not settings:
        st.warning('The settings for this run are not available, so its outputs cannot be shown.')
        return

    with st.spinner('Loading results...'):
        outputs = analysis_files(ctx.ci, analysis, 'output_file')
        inputs = analysis_files(ctx.ci, analysis, 'input_file')
    locations = inputs.get('location.csv', inputs.get('location.parquet'))
    render_results(settings, outputs, locations, key=analysis['id'])

    zip_key = f"zip_{analysis['id']}_{analysis.get('modified')}"
    if zip_key not in st.session_state:
        if st.button('Prepare results download (.zip)', key=f'{key}_{zip_key}_prep'):
            with st.spinner('Fetching outputs...'):
                st.session_state[zip_key] = ctx.ci.download_output_zip(analysis['id'])
            st.rerun()
    else:
        st.download_button('Download results (.zip)', st.session_state[zip_key], type='primary',
                           icon=':material/download:', key=f'{key}_{zip_key}_dl',
                           file_name=f"{display_name(analysis['name'])}.zip".replace(' ', '_'))
