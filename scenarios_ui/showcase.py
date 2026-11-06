"""Showcase: curated, pre-computed scenario runs that anyone can explore without waiting."""
import streamlit as st

from modules.scenarios import VISITOR_PARAM, showcase_analyses
from pages.components.data import cached_model_settings
from scenarios_ui.common import Context, analysis_results, footer, vulnerability_note

ctx = Context()
ci = ctx.ci

models = ci.models.get()
models_by_id = {m['id']: m for m in models}
portfolios_by_id = {p['id']: p for p in ci.portfolios.get()}
showcase = [a for a in showcase_analyses(ci.analyses.get(), ctx.limits, models, ctx.ui_config) if a['status'] == 'RUN_COMPLETED']

st.title('Showcase')
st.markdown('Results from scenarios we have already run for you, so you can explore what Oasis produces '
            'without waiting for a run. To run a scenario yourself, use **Run a scenario**.')

if not showcase:
    st.info('No showcase results are available yet. They are added when the service is set up.')
    footer(ctx.ui_config)
    st.stop()

titles = {a['id']: ctx.run_title(a, models_by_id) for a in showcase}
showcase.sort(key=lambda a: titles[a['id']].lower())
ids = [a['id'] for a in showcase]
by_id = {a['id']: a for a in showcase}
selected_id = st.selectbox('Scenario', ids, format_func=lambda i: titles[i],
                           key='showcase_selected')
analysis = by_id[selected_id]

model = models_by_id.get(analysis['model'])
if model is not None:
    description = cached_model_settings(ci, model).get('description')
    if description:
        st.caption(description)
    vulnerability_note(cached_model_settings(ci, model))
    if st.button('Run this scenario yourself', icon=':material/play_circle:'):
        st.session_state['sc_model_id'] = model['id']
        st.session_state['sc_portfolio_id'] = analysis['portfolio']
        st.switch_page('scenarios_ui/explore.py', query_params={VISITOR_PARAM: ctx.vid})

analysis_results(ctx, analysis, models_by_id, portfolios_by_id, key='showcase')
footer(ctx.ui_config)
