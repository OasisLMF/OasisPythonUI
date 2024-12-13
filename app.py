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

portfolios = client.portfolios.get().json()
portfolios =  pd.json_normalize(portfolios)

date_time_cols = ['created', 'modified']
portfolios = convert_datetime_cols(portfolios, date_time_cols)

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

display_cols = [ 'id', 'name', 'created', 'modified', 'storage_links', ]

column_config = generate_column_config(portfolios.columns.values, display_cols,
                                       date_time_cols=date_time_cols)

st.dataframe(portfolios, hide_index=True, column_config=column_config, column_order=display_cols)

"### Create New Portfolio"

def validate_name(name):
    if not name or len(name) == 0:
        return False, f"Name is required"
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
            st.write("Form submitted successfully")
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

        else:
            st.write("Form not submitted")
new_portfolio()

"## Analyses"

analyses = client.analyses.get().json()
analyses = pd.json_normalize(analyses)
analyses = convert_datetime_cols(analyses, date_time_cols)

# Following need to be combined with other df
# - Portfolio Name
# - Model Version
# - Supplier
# - Created
# - Modified
# - Status Details
# - Status

display_cols = [ 'id', 'name', 'portfolio', 'model', 'created', 'modified',
                'status' ]

column_config = generate_column_config(analyses.columns.values, display_cols,
                                       date_time_cols=date_time_cols)

st.dataframe(analyses, hide_index=True, column_config=column_config, column_order=display_cols)
