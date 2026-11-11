import streamlit as st

from modules.ui import page_setup
from pages.components.common import (ANALYSES_PAGE, NEW_ANALYSIS_DEFAULTS, SELECTED_ANALYSIS,
                                     SELECTED_MODEL, open_record, selectable_table)
from pages.components.data import analyses_df, cached_model_settings, models_df
from pages.components.model_details import model_details

ci = page_setup('Models')

models = ci.models.get()
analyses = ci.analyses.get()
models_by_id = {m['id']: m for m in models}

st.caption('Models registered on this platform. Select one to see its settings, '
           'run options and the analyses that have used it.')

if not models:
    st.info('No models are registered on this platform.')
    st.stop()

table = models_df(ci, models, analyses)
column_config = {
    'name': 'Name',
    'id': st.column_config.NumberColumn('ID', width='small'),
    'supplier_id': 'Supplier',
    'model_id': 'Model ID',
    'version_id': 'Version',
    'run_mode': st.column_config.TextColumn('Run mode', width='small'),
    'n_analyses': st.column_config.NumberColumn('Analyses', width='small'),
}
selected_id = selectable_table(table, ['id', 'name', 'supplier_id', 'model_id', 'version_id',
                                       'run_mode', 'n_analyses'],
                               SELECTED_MODEL, column_config)

if selected_id is None:
    st.caption('Select a model above to see its details.')
    st.stop()

model = models_by_id[selected_id]
settings = cached_model_settings(ci, model)
model_analyses = [a for a in analyses if a['model'] == selected_id]

st.divider()
title_col, action_col = st.columns([0.8, 0.2], vertical_alignment='bottom')
title_col.subheader(settings.get('name') or model['model_id'])
if action_col.button('New analysis', icon=':material/play_arrow:', width='stretch',
                     help='Create an analysis using this model'):
    st.session_state[NEW_ANALYSIS_DEFAULTS] = {'model': selected_id}
    st.switch_page(ANALYSES_PAGE)

details_col, analyses_col = st.columns([0.62, 0.38], gap='large')

with details_col:
    model_details(model, settings)

with analyses_col:
    st.markdown(f'**Analyses using this model ({len(model_analyses)})**')
    if not model_analyses:
        st.caption('None yet.')
    else:
        a_table = analyses_df(model_analyses, ci.portfolios.get(), table)
        open_id = selectable_table(
            a_table, ['name', 'portfolio_name', 'status_label'], 'model_open_analysis',
            {'name': 'Analysis', 'portfolio_name': 'Portfolio', 'status_label': 'Status'},
            key=f'model_analyses_{selected_id}')
        if st.button('Open analysis', disabled=open_id is None, icon=':material/open_in_new:'):
            open_record(ANALYSES_PAGE, SELECTED_ANALYSIS, open_id)
