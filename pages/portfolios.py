import streamlit as st
from requests.exceptions import HTTPError

from modules.ui import flash, page_setup, show_api_error
from pages.components.common import (ANALYSES_PAGE, NEW_ANALYSIS_DEFAULTS, SELECTED_ANALYSIS,
                                     SELECTED_PORTFOLIO, open_record, selectable_table)
from pages.components.data import (FILE_TYPES, analyses_df, guess_file_type, models_df,
                                   portfolio_file_df, portfolios_df)
from pages.components.exposure import exposure_overview

ci = page_setup('Portfolios')

portfolios = ci.portfolios.get()
analyses = ci.analyses.get()
portfolios_by_id = {p['id']: p for p in portfolios}


##########################################################################################
# Create portfolio
##########################################################################################

@st.dialog('New portfolio', width='large')
def create_portfolio_dialog():
    name = st.text_input('Portfolio name', key='new_portfolio_name')
    uploads = st.file_uploader('OED files (CSV or parquet)', accept_multiple_files=True,
                               type=['csv', 'parquet'], key='new_portfolio_files')
    by_name = {f.name: f for f in uploads}

    assignment = {}
    if uploads:
        st.caption('Check which file is which. Guessed from the file names.')
        guesses = {guess_file_type(f.name): f.name for f in reversed(uploads)}
        options = list(by_name)
        for file_type, label in FILE_TYPES.items():
            guess = guesses.get(file_type)
            choice = st.selectbox(f'{label} file', options,
                                  index=options.index(guess) if guess else None,
                                  placeholder='None', key=f'new_portfolio_{file_type}')
            if choice:
                assignment[file_type] = by_name[choice]

    problems = []
    if not name:
        problems.append('Enter a portfolio name.')
    if name and name in [p['name'] for p in portfolios]:
        problems.append(f'A portfolio called "{name}" already exists.')
    if 'location_file' not in assignment:
        problems.append('A location file is required.')
    chosen = [f.name for f in assignment.values()]
    if len(chosen) != len(set(chosen)):
        problems.append('Each uploaded file can only be used once.')

    for p in problems:
        st.caption(f':orange[{p}]')

    if st.button('Create portfolio', type='primary', disabled=bool(problems)):
        try:
            with st.spinner('Uploading...'):
                created = ci.portfolios.create(
                    name=name, **assignment)
            st.session_state[SELECTED_PORTFOLIO] = (created or {}).get('id')
            flash(f'Portfolio "{name}" created')
            st.rerun()
        except HTTPError as e:
            show_api_error('Creating portfolio', e)


##########################################################################################
# Portfolio list
##########################################################################################

header_left, header_right = st.columns([0.8, 0.2], vertical_alignment='bottom')
header_left.caption('Portfolios are sets of OED exposure files. Select one to view or change its files, '
                    'explore its exposure, or see the analyses run against it.')
if header_right.button('New portfolio', type='primary', icon=':material/add:', width='stretch'):
    create_portfolio_dialog()

if not portfolios:
    st.info('No portfolios yet. Create one to get started.')
    st.stop()

table = portfolios_df(portfolios, analyses)
column_config = {
    'name': 'Name',
    'id': st.column_config.NumberColumn('ID', width='small'),
    'location_file': st.column_config.CheckboxColumn('Location', width='small'),
    'accounts_file': st.column_config.CheckboxColumn('Accounts', width='small'),
    'reinsurance_info_file': st.column_config.CheckboxColumn('RI info', width='small'),
    'reinsurance_scope_file': st.column_config.CheckboxColumn('RI scope', width='small'),
    'n_analyses': st.column_config.NumberColumn('Analyses', width='small'),
    'modified': st.column_config.DatetimeColumn('Modified', format='D MMM YYYY, HH:mm'),
}
selected_id = selectable_table(table.sort_values('id', ascending=False),
                               ['id', 'name', *FILE_TYPES, 'n_analyses', 'modified'],
                               SELECTED_PORTFOLIO, column_config)

if selected_id is None:
    st.caption('Select a portfolio above to see its details.')
    st.stop()

portfolio = portfolios_by_id[selected_id]
portfolio_analyses = [a for a in analyses if a['portfolio'] == selected_id]


##########################################################################################
# Portfolio detail
##########################################################################################

st.divider()
title_col, *action_cols = st.columns([0.55, 0.15, 0.15, 0.15], vertical_alignment='bottom')
title_col.subheader(portfolio['name'])

with action_cols[0]:
    if st.button('New analysis', icon=':material/play_arrow:', width='stretch',
                 disabled=not (portfolio.get('location_file') or {}).get('stored'),
                 help='Create an analysis using this portfolio'):
        st.session_state[NEW_ANALYSIS_DEFAULTS] = {'portfolio': selected_id}
        st.switch_page(ANALYSES_PAGE)

with action_cols[1].popover('Rename', icon=':material/edit:', width='stretch'):
    new_name = st.text_input('New name', value=portfolio['name'], key=f'rename_{selected_id}')
    if st.button('Save', key=f'rename_save_{selected_id}', disabled=not new_name or new_name == portfolio['name']):
        try:
            ci.portfolios.rename(selected_id, new_name)
            flash('Portfolio renamed')
            st.rerun()
        except HTTPError as e:
            show_api_error('Renaming portfolio', e)

with action_cols[2].popover('Delete', icon=':material/delete:', width='stretch'):
    if portfolio_analyses:
        st.warning(f'{len(portfolio_analyses)} analyses use this portfolio. They will lose access to its files.')
    st.write(f"Delete **{portfolio['name']}**? This cannot be undone.")
    if st.button('Delete portfolio', type='primary', key=f'delete_{selected_id}'):
        try:
            ci.portfolios.delete(selected_id)
            st.session_state[SELECTED_PORTFOLIO] = None
            flash(f"Portfolio \"{portfolio['name']}\" deleted")
            st.rerun()
        except HTTPError as e:
            show_api_error('Deleting portfolio', e)

files_tab, exposure_tab, analyses_tab = st.tabs(
    ['Files', 'Exposure', f'Analyses ({len(portfolio_analyses)})'])


with files_tab:
    for file_type, label in FILE_TYPES.items():
        info = portfolio.get(file_type) or {}
        attached = bool(info.get('stored'))

        with st.container(border=True):
            name_col, status_col, *btn_cols = st.columns([0.2, 0.35, 0.15, 0.15, 0.15],
                                                         vertical_alignment='center')
            name_col.markdown(f'**{label}**')
            status_col.markdown(f"`{info.get('name')}`" if attached else ':grey[Not attached]')

            preview_key = f'preview_{selected_id}_{file_type}'
            if attached and btn_cols[0].button('Hide' if st.session_state.get(preview_key) else 'Preview',
                                               key=f'{preview_key}_btn', width='stretch'):
                st.session_state[preview_key] = not st.session_state.get(preview_key, False)
                st.rerun()

            with btn_cols[1].popover('Replace' if attached else 'Attach', width='stretch'):
                upload = st.file_uploader(f'{label} file', type=['csv', 'parquet'],
                                          key=f'upload_{selected_id}_{file_type}')
                if st.button('Upload', key=f'upload_btn_{selected_id}_{file_type}', disabled=upload is None):
                    try:
                        ci.portfolios.upload_file(selected_id, file_type, upload.getvalue(), upload.name)
                        flash(f'{label} file uploaded')
                        st.rerun()
                    except HTTPError as e:
                        show_api_error(f'Uploading {label.lower()} file', e)

            if attached:
                with btn_cols[2].popover('Remove', width='stretch'):
                    st.write(f'Remove the {label.lower()} file from this portfolio?')
                    if st.button('Remove', type='primary', key=f'remove_{selected_id}_{file_type}'):
                        try:
                            ci.portfolios.delete_file(selected_id, file_type)
                            flash(f'{label} file removed')
                            st.rerun()
                        except HTTPError as e:
                            show_api_error(f'Removing {label.lower()} file', e)

            if attached and st.session_state.get(preview_key):
                with st.spinner('Loading file...'):
                    df = portfolio_file_df(ci, portfolio, file_type)
                if df is not None:
                    st.caption(f'{len(df):,} rows × {df.shape[1]} columns')
                    st.dataframe(df.head(1000), hide_index=True, height=300)
                    st.download_button('Download CSV', df.to_csv(index=False).encode(),
                                       file_name=info.get('name') or f'{file_type}.csv',
                                       key=f'download_{selected_id}_{file_type}')


with exposure_tab:
    if not (portfolio.get('location_file') or {}).get('stored'):
        st.info('Attach a location file to see an exposure summary.')
    else:
        with st.spinner('Loading locations...'):
            locations = portfolio_file_df(ci, portfolio, 'location_file')
        exposure_overview(locations)


with analyses_tab:
    if not portfolio_analyses:
        st.info('No analyses have been run against this portfolio.')
    else:
        a_table = analyses_df(portfolio_analyses, portfolios, models_df(ci, ci.models.get()))
        open_id = selectable_table(
            a_table, ['name', 'model_name', 'status_label', 'modified'], 'portfolio_open_analysis',
            {'name': 'Analysis', 'model_name': 'Model', 'status_label': 'Status',
             'modified': st.column_config.DatetimeColumn('Modified', format='D MMM YYYY, HH:mm')},
            key=f'portfolio_analyses_{selected_id}')
        if st.button('Open analysis', disabled=open_id is None, icon=':material/open_in_new:'):
            open_record(ANALYSES_PAGE, SELECTED_ANALYSIS, open_id)
