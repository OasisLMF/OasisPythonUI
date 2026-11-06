"""Run a scenario: choose a scenario and its exposure, run it, and view the results."""
from datetime import datetime, timezone

import pandas as pd
import streamlit as st
from oasis_data_manager.errors import OasisException
from requests.exceptions import HTTPError

from modules.scenarios import (GROUP_BY_OPTIONS, display_name, is_active, limit_processes, run_blocked_reason,
                               scenario_models, scenario_portfolios, tagged_name, visitor_analyses,
                               visitor_tag)
from modules.ui import api_error_message, flash, show_flash
from pages.components.common import analysis_progress, current_task, format_status
from pages.components.data import cached_model_settings, portfolio_file_df
from pages.components.exposure import exposure_overview
from scenarios_ui.common import Context, analysis_results, footer, run_settings

SELECTED_MODEL = 'sc_model_id'
SELECTED_PORTFOLIO = 'sc_portfolio_id'
SELECTED_RUN = 'sc_run_id'

ctx = Context()
ci = ctx.ci
show_flash()

models = ci.models.get()
portfolios = ci.portfolios.get()
analyses = ci.analyses.get()
models_by_id = {m['id']: m for m in models}
portfolios_by_id = {p['id']: p for p in portfolios}
my_runs = sorted(visitor_analyses(analyses, ctx.vid), key=lambda a: a['id'], reverse=True)

st.title('Run a scenario')
st.markdown(
    'Estimate the losses a real or realistic disaster could cause to a pre-loaded portfolio of '
    'buildings, using the open-source [Oasis](https://oasislmf.org/) loss modelling framework. '
    'Choose a scenario, check the exposure it will be run against, then run it and explore the results.')

scenarios = sorted(scenario_models(models, portfolios, ctx.ui_config), key=ctx.scenario_name)
if not scenarios:
    st.warning('No scenarios are available at the moment. Please check back later.')
    footer(ctx.ui_config)
    st.stop()


##########################################################################################
# 1. Scenario
##########################################################################################

st.header('1. Choose a scenario', divider='gray')
selected_model_id = st.session_state.get(SELECTED_MODEL)

cols_per_row = 3
for start in range(0, len(scenarios), cols_per_row):
    cols = st.columns(cols_per_row)
    for col, model in zip(cols, scenarios[start:start + cols_per_row]):
        settings = cached_model_settings(ci, model)
        selected = model['id'] == selected_model_id
        with col.container(border=True, height=200):
            st.markdown(f"**{ctx.scenario_name(model)}**")
            st.caption(f"Provided by {model['supplier_id']}")
            description = settings.get('description') or ''
            st.write(description if len(description) <= 160 else description[:157] + '...')
        if col.button('Selected' if selected else 'Choose this scenario', key=f"choose_{model['id']}",
                      type='primary' if selected else 'secondary', width='stretch', disabled=selected,
                      icon=':material/check:' if selected else None):
            st.session_state[SELECTED_MODEL] = model['id']
            st.session_state[SELECTED_PORTFOLIO] = None
            st.rerun()

model = models_by_id.get(selected_model_id)


##########################################################################################
# 2. Exposure
##########################################################################################

portfolio = None
locations = None
if model is not None:
    st.header('2. Check the exposure', divider='gray')
    model_settings = cached_model_settings(ci, model)
    with st.expander(f'About {ctx.scenario_name(model)}'):
        st.write(model_settings.get('description') or 'No description provided.')
        perils = model_settings.get('lookup_settings', {}).get('supported_perils', [])
        if perils:
            st.markdown('**Perils:** ' + ', '.join(f"{p.get('desc', p['id'])} (`{p['id']}`)" for p in perils))

    options = scenario_portfolios(model, portfolios, ctx.ui_config)
    if len(options) > 1:
        ids = [p['id'] for p in options]
        current = st.session_state.get(SELECTED_PORTFOLIO)
        portfolio_id = st.radio('Exposure portfolio', ids, horizontal=True,
                                index=ids.index(current) if current in ids else 0,
                                format_func=lambda i: portfolios_by_id[i]['name'],
                                help='The buildings the scenario will be run against.')
    else:
        portfolio_id = options[0]['id']
    st.session_state[SELECTED_PORTFOLIO] = portfolio_id
    portfolio = portfolios_by_id[portfolio_id]

    st.caption(f"The scenario will be run against the **{portfolio['name']}** portfolio. "
               'You cannot upload your own exposure in this tool.')
    with st.spinner('Loading exposure...'):
        try:
            locations = portfolio_file_df(ci, portfolio, 'location_file')
        except (HTTPError, OasisException):
            locations = None
    if locations is not None:
        exposure_overview(locations, breakdowns=False)


##########################################################################################
# 3. Run
##########################################################################################

if model is not None and portfolio is not None:
    st.header('3. Run', divider='gray')
    limits = ctx.limits

    left, right = st.columns(2)
    samples = left.slider(
        'Number of samples', min_value=1, max_value=limits.max_samples, value=limits.default_samples,
        help='Damage to each building is uncertain. Each sample is one possible outcome of the scenario; '
             'averaging over more samples gives a more reliable estimate but takes longer. The results also '
             'show the model\'s analytical mean, which does not depend on the number of samples.')

    available = set(locations.columns) if locations is not None else set()
    if (portfolio.get('accounts_file') or {}).get('stored'):
        available.add('PortNumber')
    group_options = [(label, field) for label, field in GROUP_BY_OPTIONS if field in available]
    labels = right.pills('Break losses down by', [label for label, _ in group_options], selection_mode='multi',
                         help='Show losses per portfolio, country or location as well as in total.')
    group_fields = [field for label, field in group_options if label in (labels or [])]

    blocked = run_blocked_reason(analyses, ctx.vid, limits)
    if blocked:
        st.info(blocked)
    if st.button('Run scenario', type='primary', icon=':material/play_arrow:', disabled=bool(blocked)):
        name = f"{ctx.scenario_name(model)} – {portfolio['name']} ({datetime.now(timezone.utc):%d %b %H:%M} UTC)"
        try:
            with st.spinner('Starting run...'):
                settings = limit_processes(run_settings(ci, model, samples, group_fields),
                                           limits.processes_per_run)
                analysis = ci.create_analysis(portfolio['id'], model['id'], tagged_name(name, visitor_tag(ctx.vid)))
                ci.upload_settings(analysis['id'], settings)
                ci.generate_and_run(analysis['id'])
        except (HTTPError, OasisException) as e:
            st.error(f'The run could not be started. {api_error_message(e)}')
        else:
            st.session_state[SELECTED_RUN] = analysis['id']
            flash('Run started. Results will appear below when it completes.')
            st.rerun()


##########################################################################################
# Your runs
##########################################################################################

st.header('Your runs', divider='gray')
if not my_runs:
    st.caption('Runs you start appear here. They are kept for a few days.')
else:
    snapshot = {a['id']: a['status'] for a in my_runs}
    any_running = any(is_active(a) for a in my_runs)

    @st.fragment(run_every='3s' if any_running else None)
    def live_progress():
        if not any_running:
            return
        fresh = visitor_analyses(ci.analyses.get(), ctx.vid)
        if {a['id']: a['status'] for a in fresh} != snapshot:
            st.rerun()
        for a in fresh:
            if is_active(a):
                fraction, detail = analysis_progress(a)
                task = current_task(ci.analyses.sub_tasks(a['id']))
                text = ' · '.join(x for x in [f"**{display_name(a['name'])}**", format_status(a['status']),
                                              task, detail] if x)
                st.progress(fraction or 0.0, text=text)

    live_progress()

    table = pd.DataFrame([{'id': a['id'], 'Run': display_name(a['name']), 'Status': format_status(a['status'])}
                          for a in my_runs])
    ids = table['id'].tolist()

    def on_select():
        rows = st.session_state['sc_runs_table'].selection.rows
        st.session_state[SELECTED_RUN] = ids[rows[0]] if rows else None

    st.dataframe(table, key='sc_runs_table', on_select=on_select, selection_mode='single-row',
                 hide_index=True, column_order=['Run', 'Status'], width='stretch')

    selected_run = next((a for a in my_runs if a['id'] == st.session_state.get(SELECTED_RUN)), None)
    if selected_run is None:
        st.caption('Select a run to see its results.')
    else:
        analysis_results(ctx, selected_run, models_by_id, portfolios_by_id, key='explore')

footer(ctx.ui_config)
