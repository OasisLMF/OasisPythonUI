import streamlit as st
from oasislmf.platform_api.client import APIClient
import pandas as pd
from requests.exceptions import HTTPError
from modules.nav import SidebarNav
from modules.validation import validate_name, validate_not_none, validate_col_val, validate_key_is_not_null
import json
from json import JSONDecodeError

st.set_page_config(
        page_title = "Analysis"
)

SidebarNav()

"# OasisLMF UI"

@st.cache_resource
def get_client():
    return APIClient()

@st.cache_data
def selected_to_row(selected, df):
    selected = selected["selection"]["rows"]

    if len(selected) > 0:
        return df.iloc[selected[0]]
    return None

client = get_client()

"## Portfolios"


@st.cache_data
def convert_datetime_cols(df, cols):
    for c in cols:
        df[c] = pd.to_datetime(df[c])
    return df

@st.cache_data
def generate_column_config(col_names, display_cols, date_time_cols=None):
    config = {name: None for name in col_names}
    for c in display_cols:
        config[c] = c.replace('_', ' ').title()

    if date_time_cols is None:
        return config

    for c in date_time_cols:
        config[c] = st.column_config.DatetimeColumn(config[c],
                                                    format="DD/MM/YY HH:mm:ss")

    return config

date_time_cols = ['created', 'modified']

def display_portfolios(portfolios):
    display_cols = [ 'id', 'name', 'created', 'modified', 'storage_links', ]
    if portfolios.empty:
        column_config = generate_column_config(display_cols, display_cols)
        st.dataframe(pd.DataFrame(columns=display_cols), hide_index=True, column_config=column_config,
                     column_order=display_cols)
        return None

    portfolios = convert_datetime_cols(portfolios, date_time_cols)

    column_config = generate_column_config(portfolios.columns.values, display_cols,
                                           date_time_cols=date_time_cols)

    st.dataframe(portfolios, hide_index=True, column_config=column_config, column_order=display_cols,
                 use_container_width=True)

show_portfolio, create_portfolio = st.tabs(['Show Portfolios', 'Create Portfolio'])

with show_portfolio:
    portfolios = client.portfolios.get().json()
    portfolios =  pd.json_normalize(portfolios)
    display_portfolios(portfolios)

@st.fragment
def new_portfolio():
    files = st.file_uploader("Upload portfolio files", accept_multiple_files=True)
    filesDict = { f.name: f for f in files}

    options = [f.name for f in files]

    if 'portfolio_form_data' not in st.session_state:
        st.session_state.portfolio_form_data = {
            'name': None,
            'location_file': None,
            'accounts_file': None,
            'reinsurance_info_file': None,
            'reinsurance_scope_file': None,
            'submitted': False
        }

    with st.form("create_portfolio_form", clear_on_submit=True, enter_to_submit=False):
        name = st.text_input('Portfolio Name', value=None)
        loc_file = st.selectbox('Select Location File', options, index=None)
        acc_file = st.selectbox('Select Accounts File', options, index=None)
        ri_file = st.selectbox('Select Reinsurance Info File', options, index=None)
        rs_file = st.selectbox('Select Reinsurance Scope File', options, index=None)

        submitted = st.form_submit_button("Create Portfolio")

        if submitted:
            validation = validate_name(name)
            if validation[0]:
                st.session_state.portfolio_form_data.update({
                    'name': name,
                    'location_file': loc_file,
                    'accounts_file': acc_file,
                    'reinsurance_info_file': ri_file,
                    'reinsurance_scope_file': rs_file,
                    'submitted': True
                })
            else:
                st.error(validation[1])
                submitted = False

        if submitted:
            form_data = st.session_state.portfolio_form_data
            def prepare_upload_dict(fname):
                upload_f = form_data.get(fname)
                if upload_f:
                    upload_f = {'name': upload_f, 'bytes': filesDict[upload_f]}
                return upload_f

            pname = form_data['name']
            location_f = prepare_upload_dict('location_file')
            accounts_f = prepare_upload_dict('accounts_file')
            ri_info_f = prepare_upload_dict('reinsurance_info_file')
            ri_scope_f = prepare_upload_dict('reinsurance_scope_file')

            try:
                client.upload_inputs(portfolio_name=pname,
                                     location_f = location_f,
                                     accounts_f = accounts_f,
                                     ri_info_f = ri_info_f,
                                     ri_scope_f = ri_scope_f)
                # Reset form
                st.session_state.portfolio_form_data = {
                    'name': None,
                    'location_file': None,
                    'accounts_file': None,
                    'reinsurance_info_file': None,
                    'reinsurance_scope_file': None,
                    'submitted': False
                }
            except HTTPError as e:
                st.error(e)

with create_portfolio:
    new_portfolio()

"## Analyses"

def display_analyses(analyses):
    display_cols = [ 'id', 'name', 'portfolio', 'model', 'created', 'modified',
                    'status' ]

    if analyses.empty:
        column_config = generate_column_config(display_cols, display_cols)
        st.dataframe(pd.DataFrame(columns=display_cols), hide_index=True, column_config=column_config,
                     column_order=display_cols)
        return None

    analyses = convert_datetime_cols(analyses, date_time_cols)

    # Following need to be combined with other df
    # - Portfolio Name
    # - Model Version
    # - Supplier
    # - Created
    # - Modified
    # - Status Details
    # - Status

    column_config = generate_column_config(analyses.columns.values, display_cols,
                                           date_time_cols=date_time_cols)

    selected = st.dataframe(analyses, hide_index=True,
                                     column_config=column_config,
                                     column_order=display_cols,
                                     use_container_width=True,
                                     selection_mode="single-row",
                                     on_select="rerun")
    return selected_to_row(selected, analyses)


def display_select_models(models):
    display_cols = ['id', 'supplier_id', 'model_id', 'version_id', 'created', 'modified']

    if models.empty:
        column_config = generate_column_config(display_cols, display_cols)
        st.dataframe(pd.DataFrame(columns=display_cols), hide_index=True, column_config=column_config,
                     column_order=display_cols)
        return None

    models = convert_datetime_cols(models, date_time_cols)

    column_config = generate_column_config(models.columns.values, display_cols,
                                           date_time_cols=date_time_cols)

    st.write('Select Model')
    selected = st.dataframe(models, hide_index=True, column_config=column_config, column_order=display_cols,
                     selection_mode="single-row", on_select="rerun")

    return selected_to_row(selected, models)


@st.fragment
def new_analysis():
    portfolios = client.portfolios.get().json()
    models = client.models.get().json()
    models = pd.json_normalize(models)

    def format_portfolio(portfolio):
        return f"{portfolio['id']}: {portfolio['name']}"

    with st.form("create_analysis_form", clear_on_submit=True, enter_to_submit=False):
        name = st.text_input("Analysis Name")
        portfolio = st.selectbox('Select Portfolio', options = portfolios,
                                    index=None, format_func=format_portfolio)


        model = display_select_models(models)
        submitted = st.form_submit_button("Create Analysis")

        if submitted:
            # todo: add validation requiring name
            validations = []
            validations.append(validate_name(name))
            validations.append(validate_not_none(portfolio, 'Porfolio'))
            validations.append(validate_not_none(model, 'Model'))

            if all([v[0] for v  in validations]):
                client.create_analysis(portfolio_id=int(portfolio["id"]), model_id=int(model["id"]),
                                       analysis_name=name)
            else:
                for v in validations:
                    if v[0] is False:
                        st.error(v[1])
                submitted = False

analyses = client.analyses.get().json()
analyses = pd.json_normalize(analyses)

# Tabs for show and create
show_analyses, create_analysis, upload_settings = st.tabs(['Show Analysis',
                                                           'Create Analysis',
                                                           'Upload Settings'])

selected = None
with show_analyses:
    selected = display_analyses(analyses)

# Anlaysis run buttons
    left, middle, right = st.columns(3)

    validation_list = [[validate_not_none, (selected,)],
                   [validate_col_val, (selected, 'status', 'NEW')]]

    validations = []
    for validation in validation_list:
        vfunc, vargs = validation
        validations.append(vfunc(*vargs))
        if not validations[-1][0]:
            break

    generateDisabled = True
    if all([v[0] for v in validations]):
        generateDisabeld = False

    if left.button("Generate Inputs", use_container_width=True, disabled=generateDisabled):
        try:
            client.analyses.generate(selected['id'])
        except HTTPError as e:
            st.error(e)

    validation_list = [[validate_not_none, (selected, 'Anlaysis row')],
                       [validate_col_val, (selected, 'status', 'READY')],
                       [validate_key_is_not_null, (selected, 'settings')]]
    validations = []
    for validation in validation_list:
        vfunc, vargs = validation
        validations.append(vfunc(*vargs))
        if not validations[-1][0]:
            break

    runDisabled = True
    if all([v[0] for v in validations]):
        runDisabled = False
        help = None
    else:
        help = ''
        for v in validations:
            if v[0] is False:
                help += v[1]
                help += '\n'

    if middle.button("Run", use_container_width=True, disabled=runDisabled, help=help):
        try:
            client.analyses.run(selected['id'])
        except HTTPError as e:
            st.error(e)

    # ToDo make new section for analysis settings, move Run button underneath this

with create_analysis:
    new_analysis()

def upload_settings_file():
    analyses = client.analyses.get().json()

    def format_analyses(analysis):
        return f"{analysis['id']}: {analysis['name']}"

    with st.form("upload_settings_form", clear_on_submit=True, enter_to_submit=False):
        selected = st.selectbox('Select Anlaysis', options = analyses,
                                     index=None, format_func=format_analyses)


        uploadedFile = st.file_uploader("Upload Analysis Settins JSON file")

        submitted = st.form_submit_button("Submit")

    if submitted:
        try:
            analysis_settings = json.load(uploadedFile)
            client.upload_settings(selected['id'], analysis_settings)
        except (JSONDecodeError, HTTPError) as e:
            st.error(f'Invalid Settings File: {e}')

with upload_settings:
    upload_settings_file()
