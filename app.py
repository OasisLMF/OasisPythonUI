import streamlit as st
from oasislmf.platform_api.client import APIClient
import pandas as pd
from requests.exceptions import HTTPError

"# OasisLMF UI"

@st.cache_resource
def get_client():
    return APIClient()

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

    st.dataframe(portfolios, hide_index=True, column_config=column_config, column_order=display_cols)

show_portfolio, create_portfolio = st.tabs(['Show Portfolios', 'Create Portfolio'])

with show_portfolio:
    portfolios = client.portfolios.get().json()
    portfolios =  pd.json_normalize(portfolios)
    display_portfolios(portfolios)

def validate_name(name):
    if not name or len(name) == 0:
        return False, "Name is required"
    return True, ""

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

    with st.form("create_portfolio_form", clear_on_submit=True):
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

    st.dataframe(analyses, hide_index=True, column_config=column_config, column_order=display_cols)

analyses = client.analyses.get().json()
analyses = pd.json_normalize(analyses)


show_analyses, create_analysis = st.tabs(['Show Analysis', 'Create Analysis'])

with show_analyses:
    display_analyses(analyses)

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

    selected = selected["selection"]["rows"]
    if len(selected) > 0:
        return models.iloc[selected[0]]

    return None

@st.fragment
def new_analysis():
    portfolios = client.portfolios.get().json()
    models = client.models.get().json()
    models = pd.json_normalize(models)

    def format_portfolio(portfolio):
        return f"{portfolio['id']}: {portfolio['name']}"

    with st.form("create_analysis_form", clear_on_submit=True):
        name = st.text_input("Analysis Name")
        portfolio = st.selectbox('Select Portfolio', options = portfolios,
                                    index=None, format_func=format_portfolio)


        model = display_select_models(models)
        submitted = st.form_submit_button("Create Analysis")

    if submitted:
        # todo: add validation
        st.write('Submitted')
        st.write(f'Name submitted: {name}')
        st.write(f'Portfolio submitted: {portfolio["id"]}')
        st.write(f'Model submitted: {model["id"]}')
    else:
        st.write('Not Submitted')

with create_analysis:
    new_analysis()


