import json
import logging
from pathlib import Path

import streamlit as st
from oasis_data_manager.errors import OasisException
from requests.exceptions import HTTPError

from modules.settings import get_analyses_settings
from modules.schemas import PERSPECTIVE_LABELS, PERSPECTIVES
from modules.ui import flash, page_setup, show_api_error
from pages.components.common import (ERROR_STATUSES, IN_PROGRESS_STATUSES, MODELS_PAGE,
                                     NEW_ANALYSIS_DEFAULTS, PORTFOLIOS_PAGE, SELECTED_ANALYSIS,
                                     SELECTED_MODEL, SELECTED_PORTFOLIO, analysis_progress,
                                     format_status, open_record, selectable_table)
from pages.components.data import (analyses_df, analysis_files, analysis_settings,
                                   cached_model_settings, model_label, models_df, session_cached)
from pages.components.logs import display_traceback_file
from pages.components.results import render_results
from pages.components.settings_editor import analysis_settings_editor, reset_editor

logger = logging.getLogger(__name__)

ci = page_setup('Analyses')

VIEW_KEY = 'analyses_view'   # None (list), 'new', or ('edit', analysis_id)
RUNNABLE_WITH_INPUTS = ['READY', 'RUN_COMPLETED', 'RUN_CANCELLED', 'RUN_ERROR']

if st.session_state.get(NEW_ANALYSIS_DEFAULTS) is not None:
    st.session_state[VIEW_KEY] = 'new'

portfolios = ci.portfolios.get()
models = ci.models.get()
analyses = ci.analyses.get()
portfolios_by_id = {p['id']: p for p in portfolios}
models_by_id = {m['id']: m for m in models}
analyses_by_id = {a['id']: a for a in analyses}
models_table = models_df(ci, models)


def close_editor(editor_key=None):
    if editor_key:
        reset_editor(editor_key)
    st.session_state[VIEW_KEY] = None
    st.session_state[NEW_ANALYSIS_DEFAULTS] = None


def start_run(analysis, regenerate=False):
    '''Run an analysis, generating inputs first if needed.'''
    if regenerate or analysis['status'] not in RUNNABLE_WITH_INPUTS:
        ci.generate_and_run(analysis['id'])
    else:
        ci.run(analysis['id'])


##########################################################################################
# Settings templates
##########################################################################################

def template_picker(model, key, current=None):
    '''Choose what to base the analysis settings on.

    Returns:
        (source_id, settings) — settings is None for "model defaults".
    '''
    sources = {}
    if current:
        sources['current'] = ('Current analysis settings', lambda: current)

    try:
        templates = ci.models.setting_templates.get(model['id']) or []
    except (HTTPError, OasisException, AttributeError) as e:
        logger.warning(f'No setting templates for model {model["id"]}: {e}')
        templates = []
    for t in sorted(templates, key=lambda t: t['id'], reverse=True):
        sources[f"template_{t['id']}"] = (
            f"Template: {t.get('name') or t['id']}",
            lambda t=t: ci.models.setting_templates.get_contents(model['id'], t['id']))

    for path in get_analyses_settings(model_name_id=model['model_id'], supplier_id=model['supplier_id']):
        sources[f'file_{path}'] = (f'Default file: {Path(path).name}',
                                   lambda path=path: json.loads(Path(path).read_text()))

    for a in sorted(analyses, key=lambda a: a['id'], reverse=True):
        if a['model'] == model['id'] and a.get('settings') and (not current or a['id'] != current.get('_id')):
            # `modified` in the id so an edited analysis isn't served from cache
            sources[f"analysis_{a['id']}_{a.get('modified')}"] = (f"Copy of analysis: {a['name']}",
                                              lambda a=a: analysis_settings(ci, a))

    sources['model'] = ('Model defaults', lambda: None)
    sources['upload'] = ('Upload a settings file…', None)

    choice = st.selectbox('Start from', list(sources), format_func=lambda s: sources[s][0],
                          key=f'{key}_template',
                          help='Settings to pre-fill the form with. You can change anything afterwards.')

    if choice == 'upload':
        upload = st.file_uploader('analysis_settings.json', type=['json'], key=f'{key}_upload')
        if upload is None:
            return choice, None
        try:
            return f'upload_{upload.file_id}', json.load(upload)
        except json.JSONDecodeError as e:
            st.error(f'Could not read the settings file: {e}')
            return choice, None

    if choice == 'current':
        return choice, current
    try:
        base = session_cached(('template', model['id'], choice), sources[choice][1])
    except (HTTPError, OasisException, OSError, json.JSONDecodeError) as e:
        st.error(f'Could not load "{sources[choice][0]}": {e}')
        base = None
    return choice, base


##########################################################################################
# New analysis
##########################################################################################

def new_analysis_view():
    defaults = st.session_state.get(NEW_ANALYSIS_DEFAULTS) or {}

    title_col, back_col = st.columns([0.85, 0.15], vertical_alignment='bottom')
    title_col.subheader('New analysis')
    if back_col.button('Cancel', icon=':material/close:', width='stretch'):
        close_editor()
        st.rerun()

    usable = [p for p in portfolios if (p.get('location_file') or {}).get('stored')]
    if not usable or not models:
        st.warning('You need a portfolio with a location file and at least one model to create an analysis.')
        if not usable and st.button('Go to Portfolios'):
            close_editor()
            st.switch_page(PORTFOLIOS_PAGE)
        return

    portfolio_ids = [p['id'] for p in usable]
    model_ids = [m['id'] for m in models]

    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        portfolio_id = c1.selectbox(
            'Portfolio', portfolio_ids,
            index=portfolio_ids.index(defaults['portfolio']) if defaults.get('portfolio') in portfolio_ids
            else (0 if len(portfolio_ids) == 1 else None),
            format_func=lambda i: portfolios_by_id[i]['name'], placeholder='Choose a portfolio',
            key='new_analysis_portfolio')
        model_id = c2.selectbox(
            'Model', model_ids,
            index=model_ids.index(defaults['model']) if defaults.get('model') in model_ids
            else (0 if len(model_ids) == 1 else None),
            format_func=lambda i: model_label(models_by_id[i], cached_model_settings(ci, models_by_id[i])),
            placeholder='Choose a model', key='new_analysis_model')

        suggested = ''
        if portfolio_id and model_id:
            suggested = (f"{portfolios_by_id[portfolio_id]['name']} – "
                         f"{cached_model_settings(ci, models_by_id[model_id]).get('name') or models_by_id[model_id]['model_id']}")
        name = c3.text_input('Analysis name', placeholder=suggested or 'Name',
                             help='Leave blank to use the suggested name.', key='new_analysis_name')
        name = name.strip() or suggested

    if portfolio_id is None or model_id is None:
        st.caption('Choose a portfolio and a model to set up the analysis.')
        return

    model, portfolio = models_by_id[model_id], portfolios_by_id[portfolio_id]
    model_settings = cached_model_settings(ci, model)

    st.markdown('#### Settings')
    source, base = template_picker(model, f'new_{model_id}')
    editor_key = f'new_{portfolio_id}_{model_id}_{source}'
    settings, valid, problems = analysis_settings_editor(model, model_settings, portfolio, base, editor_key)

    st.divider()
    if problems:
        st.caption(f':orange[{len(problems)} problem(s) to fix — see the Review tab.]')
    run_col, create_col, _ = st.columns([0.2, 0.2, 0.6])
    run = run_col.button('Create and run', type='primary', icon=':material/play_arrow:',
                         disabled=not valid or not name, width='stretch')
    create = create_col.button('Create only', disabled=not valid or not name, width='stretch',
                               help='Create the analysis and save its settings without running it.')

    if run or create:
        try:
            with st.spinner('Creating analysis...'):
                analysis = ci.create_analysis(portfolio_id, model_id, name)
                ci.upload_settings(analysis['id'], settings)
                if run:
                    ci.generate_and_run(analysis['id'])
        except (HTTPError, OasisException) as e:
            show_api_error('Creating analysis', e)
            return
        st.session_state[SELECTED_ANALYSIS] = analysis['id']
        flash(f'Analysis "{name}" ' + ('created and started' if run else 'created'))
        close_editor(editor_key)
        st.rerun()


##########################################################################################
# Edit settings
##########################################################################################

def edit_settings_view(analysis):
    title_col, back_col = st.columns([0.85, 0.15], vertical_alignment='bottom')
    title_col.subheader(f"Settings: {analysis['name']}")
    if back_col.button('Cancel', icon=':material/close:', width='stretch'):
        close_editor()
        st.rerun()

    model = models_by_id.get(analysis['model'])
    portfolio = portfolios_by_id.get(analysis['portfolio'])
    if model is None or portfolio is None:
        st.error('The model or portfolio for this analysis no longer exists.')
        return
    model_settings = cached_model_settings(ci, model)

    current = analysis_settings(ci, analysis)
    if current:
        current = {**current, '_id': analysis['id']}
    source, base = template_picker(model, f"edit_{analysis['id']}", current)
    if base:
        base = {k: v for k, v in base.items() if k != '_id'}
    editor_key = f"edit_{analysis['id']}_{source}"
    settings, valid, problems = analysis_settings_editor(model, model_settings, portfolio, base, editor_key)

    st.divider()
    in_progress = analysis['status'] in IN_PROGRESS_STATUSES
    if in_progress:
        st.caption(':orange[The analysis is running. Settings can be changed once it finishes.]')
    elif problems:
        st.caption(f':orange[{len(problems)} problem(s) to fix — see the Review tab.]')
    run_col, save_col, _ = st.columns([0.2, 0.2, 0.6])
    run = run_col.button('Save and run', type='primary', icon=':material/play_arrow:',
                         disabled=not valid or in_progress, width='stretch')
    save = save_col.button('Save', disabled=not valid or in_progress, width='stretch')

    if run or save:
        try:
            ci.upload_settings(analysis['id'], settings)
            if run:
                # Regenerate inputs: model options can affect input generation
                start_run(analysis, regenerate=True)
        except (HTTPError, OasisException) as e:
            show_api_error('Saving settings', e)
            return
        flash('Settings saved' + (' and run started' if run else ''))
        close_editor(editor_key)
        st.rerun()


##########################################################################################
# Analysis list and detail
##########################################################################################

def settings_summary(settings):
    left, right = st.columns(2)
    left.metric('Samples', settings.get('number_of_samples', '—'))
    perspectives = [PERSPECTIVE_LABELS[p] for p in PERSPECTIVES if settings.get(f'{p}_output')]
    right.metric('Perspectives', len(perspectives), help=', '.join(perspectives))
    if settings.get('model_settings'):
        st.markdown('**Model options**')
        st.dataframe([{'Option': k, 'Value': json.dumps(v) if isinstance(v, (list, dict)) else str(v)}
                      for k, v in settings['model_settings'].items()], hide_index=True)
    rows = []
    for p in PERSPECTIVES:
        if not settings.get(f'{p}_output'):
            continue
        for level in settings.get(f'{p}_summaries', []):
            ords = [k for k, v in level.get('ord_output', {}).items() if v is True and k != 'parquet_format']
            legacy = [k for k in ['eltcalc', 'aalcalc', 'pltcalc', 'lec_output'] if level.get(k)]
            rows.append({'Perspective': p.upper(), 'Level': level.get('id'),
                         'Group by': ', '.join(level.get('oed_fields') or []) or 'Portfolio total',
                         'Outputs': ', '.join(ords + legacy)})
    if rows:
        st.markdown('**Outputs**')
        st.dataframe(rows, hide_index=True)


def results_tab(analysis, settings):
    if analysis['status'] != 'RUN_COMPLETED':
        st.info('Results appear here once the analysis has run successfully.')
        return
    if not settings:
        st.warning('No analysis settings found, so outputs cannot be interpreted.')
        return
    with st.spinner('Loading outputs...'):
        outputs = analysis_files(ci, analysis, 'output_file')
        inputs = analysis_files(ci, analysis, 'input_file')
    locations = inputs.get('location.csv', inputs.get('location.parquet'))
    render_results(settings, outputs, locations)

    st.divider()
    st.markdown('**Output files**')
    file_col, dl_col = st.columns([0.6, 0.4], vertical_alignment='bottom')
    fname = file_col.selectbox('File', sorted(outputs), key=f"out_file_{analysis['id']}")
    if fname:
        dl_col.download_button('Download', outputs[fname].to_csv(index=False).encode(),
                               file_name=fname, key=f"dl_out_{analysis['id']}")
    zip_key = f"zip_{analysis['id']}_{analysis.get('modified')}"
    if zip_key not in st.session_state:
        if st.button('Prepare download of all outputs (.zip)', key=f'{zip_key}_prep'):
            with st.spinner('Fetching outputs...'):
                st.session_state[zip_key] = ci.download_output_zip(analysis['id'])
            st.rerun()
    else:
        st.download_button('Download all outputs (.zip)', st.session_state[zip_key],
                           file_name=f"analysis_{analysis['id']}_output.zip", key=f'{zip_key}_dl',
                           type='primary', icon=':material/download:')


def inputs_tab(analysis):
    if analysis['status'] in ['NEW', 'INPUTS_GENERATION_QUEUED', 'INPUTS_GENERATION_STARTED',
                              'INPUTS_GENERATION_ERROR', 'INPUTS_GENERATION_CANCELLED']:
        st.info('Input files appear here once input generation has completed.')
        return
    load_key = f"show_inputs_{analysis['id']}"
    if not st.session_state.get(load_key):
        if st.button('Load generated input files', key=f'{load_key}_btn'):
            st.session_state[load_key] = True
            st.rerun()
        return
    with st.spinner('Loading inputs...'):
        inputs = analysis_files(ci, analysis, 'input_file')
    fname = st.selectbox('File', sorted(inputs), key=f"in_file_{analysis['id']}")
    if fname:
        df = inputs[fname]
        st.caption(f'{len(df):,} rows')
        st.dataframe(df.head(1000), hide_index=True, height=300)
        st.download_button('Download', df.to_csv(index=False).encode(), file_name=fname,
                           key=f"dl_in_{analysis['id']}")


def logs_tab(analysis):
    shown = False
    for kind in ['input_generation', 'run']:
        tb = ci.analyses.get_traceback(analysis['id'], kind)
        if tb:
            shown = True
            display_traceback_file(tb, trace_type=kind)
    if not shown:
        st.info('No error logs for this analysis.')


def analysis_detail(analysis):
    status = analysis['status']
    portfolio = portfolios_by_id.get(analysis['portfolio'], {})
    model = models_by_id.get(analysis['model'], {})
    in_progress = status in IN_PROGRESS_STATUSES

    title_col, *btn_cols = st.columns([0.52, 0.12, 0.12, 0.12, 0.12], vertical_alignment='bottom')
    title_col.subheader(analysis['name'])

    settings = analysis_settings(ci, analysis)
    ran_before = status not in ['NEW', 'INPUTS_GENERATION_ERROR', 'INPUTS_GENERATION_CANCELLED', 'READY']
    if btn_cols[0].button('Re-run' if ran_before else 'Run', type='primary', icon=':material/play_arrow:',
                          disabled=in_progress or not settings, width='stretch',
                          help=None if settings else 'Set up the analysis settings first.'):
        try:
            start_run(analysis)
            flash('Run started')
            st.rerun()
        except (HTTPError, OasisException) as e:
            show_api_error('Starting run', e)

    if btn_cols[1].button('Settings', icon=':material/tune:', width='stretch', disabled=in_progress):
        st.session_state[VIEW_KEY] = ('edit', analysis['id'])
        st.rerun()

    if in_progress:
        if btn_cols[2].button('Cancel', icon=':material/stop:', width='stretch'):
            try:
                ci.analyses.cancel(analysis['id'])
                flash('Cancellation requested', icon='⛔')
                st.rerun()
            except (HTTPError, OasisException) as e:
                show_api_error('Cancelling', e)

    with btn_cols[3].popover('Delete', icon=':material/delete:', width='stretch', disabled=in_progress):
        st.write(f"Delete **{analysis['name']}**? This cannot be undone.")
        if st.button('Delete analysis', type='primary', key=f"delete_{analysis['id']}"):
            try:
                ci.analyses.delete(analysis['id'])
                st.session_state[SELECTED_ANALYSIS] = None
                flash(f"Analysis \"{analysis['name']}\" deleted")
                st.rerun()
            except (HTTPError, OasisException) as e:
                show_api_error('Deleting analysis', e)

    link_cols = st.columns([0.5, 0.5])
    if link_cols[0].button(f"Portfolio: {portfolio.get('name', '—')}", type='tertiary',
                           icon=':material/folder_open:', disabled=not portfolio):
        open_record(PORTFOLIOS_PAGE, SELECTED_PORTFOLIO, portfolio['id'])
    model_name = models_table.set_index('id')['name'].get(model.get('id'), model.get('model_id', '—'))
    if link_cols[1].button(f'Model: {model_name}', type='tertiary', icon=':material/deployed_code:',
                           disabled=not model):
        open_record(MODELS_PAGE, SELECTED_MODEL, model['id'])

    if status in ERROR_STATUSES:
        st.error(f'{format_status(status)}. See the Logs tab for details.')
    if not settings and not in_progress:
        st.info('This analysis has no settings yet. Use **Settings** to set it up, then run it.')

    tabs = st.tabs(['Results', 'Settings', 'Inputs', 'Logs'])
    with tabs[0]:
        results_tab(analysis, settings)
    with tabs[1]:
        if settings:
            settings_summary(settings)
            with st.expander('Settings JSON'):
                st.json(settings, expanded=2)
            st.download_button('Download analysis_settings.json', json.dumps(settings, indent=2),
                               file_name=f"analysis_{analysis['id']}_settings.json",
                               key=f"dl_settings_{analysis['id']}")
        else:
            st.info('No settings yet.')
    with tabs[2]:
        inputs_tab(analysis)
    with tabs[3]:
        logs_tab(analysis)


def list_view():
    header_left, header_right = st.columns([0.8, 0.2], vertical_alignment='bottom')
    header_left.caption('An analysis runs a model against a portfolio with a set of analysis settings. '
                        'Select one to see its results, or create a new one.')
    if header_right.button('New analysis', type='primary', icon=':material/add:', width='stretch'):
        st.session_state[VIEW_KEY] = 'new'
        st.rerun()

    if not analyses:
        st.info('No analyses yet. Create one to get started.')
        return

    table = analyses_df(analyses, portfolios, models_table)

    f1, f2, f3, f4 = st.columns([0.3, 0.25, 0.225, 0.225])
    search = f1.text_input('Search', placeholder='Analysis name', label_visibility='collapsed')
    status_groups = {
        'In progress': IN_PROGRESS_STATUSES,
        'Completed': ['RUN_COMPLETED'],
        'Failed / cancelled': ERROR_STATUSES + ['RUN_CANCELLED', 'INPUTS_GENERATION_CANCELLED'],
        'Not run': ['NEW', 'READY'],
    }
    groups = f2.multiselect('Status', list(status_groups), placeholder='Any status',
                            label_visibility='collapsed')
    portfolio_filter = f3.selectbox('Portfolio', sorted(table['portfolio_name'].unique()),
                                    index=None, placeholder='Any portfolio', label_visibility='collapsed')
    model_filter = f4.selectbox('Model', sorted(table['model_name'].unique()),
                                index=None, placeholder='Any model', label_visibility='collapsed')

    if search:
        table = table[table['name'].str.contains(search, case=False, regex=False)]
    if groups:
        table = table[table['status'].isin(sum((status_groups[g] for g in groups), []))]
    if portfolio_filter:
        table = table[table['portfolio_name'] == portfolio_filter]
    if model_filter:
        table = table[table['model_name'] == model_filter]

    column_config = {
        'id': st.column_config.NumberColumn('ID', width='small'),
        'name': 'Name',
        'status_label': 'Status',
        'portfolio_name': 'Portfolio',
        'model_name': 'Model',
        'modified': st.column_config.DatetimeColumn('Last updated', format='D MMM YYYY, HH:mm'),
    }
    selected_id = selectable_table(table, ['id', 'name', 'status_label', 'portfolio_name', 'model_name', 'modified'],
                                   SELECTED_ANALYSIS, column_config,
                                   height=min(38 + 35 * max(len(table), 1), 400))

    snapshot = {a['id']: a['status'] for a in analyses}
    any_running = any(s in IN_PROGRESS_STATUSES for s in snapshot.values())

    @st.fragment(run_every='2s' if any_running else None)
    def live_status():
        if not any_running:
            return
        fresh = ci.analyses.get()
        if {a['id']: a['status'] for a in fresh} != snapshot:
            st.rerun()  # A status changed: refresh the whole page
        for a in fresh:
            if a['status'] not in IN_PROGRESS_STATUSES:
                continue
            fraction, detail = analysis_progress(a)
            text = f"**{a['name']}** · {format_status(a['status'])}" + (f' · {detail}' if detail else '')
            st.progress(fraction or 0.0, text=text)

    live_status()

    if selected_id is None:
        st.caption('Select an analysis above to see its details.')
        return

    st.divider()
    analysis_detail(analyses_by_id[selected_id])


##########################################################################################
# Page
##########################################################################################

view = st.session_state.get(VIEW_KEY)
if view == 'new':
    new_analysis_view()
elif isinstance(view, tuple) and view[0] == 'edit' and view[1] in analyses_by_id:
    edit_settings_view(analyses_by_id[view[1]])
else:
    list_view()
