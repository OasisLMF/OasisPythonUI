import streamlit as st
from oasislmf.platform_api.client import APIClient
import pandas as pd
from requests.exceptions import HTTPError
from modules.nav import SidebarNav
from modules.client import get_client
from modules.validation import validate_name, validate_not_none, validate_key_val, validate_key_is_not_null
import json
from json import JSONDecodeError

st.set_page_config(
    page_title = "Analysis",
    layout = "centered"
)

SidebarNav()

"# OasisLMF UI"

if st.button("♻️ "):
    st.rerun()

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
show_analyses, create_analysis = st.tabs(['Show Analysis', 'Create Analysis'])

selected = None
with show_analyses:
    selected = display_analyses(analyses)

with create_analysis:
    new_analysis()

def format_analysis(analysis):
    return f"{analysis['id']}: {analysis['name']}"

@st.dialog("Upload Settings File")
def upload_settings_file(analysis):
    with st.form("upload_settings_form", clear_on_submit=True, enter_to_submit=False):
        uploadedFile = st.file_uploader("Analysis Settings JSON file")

        submitted = st.form_submit_button("Submit")

    if submitted:
        try:
            analysis_settings = json.load(uploadedFile)
            client.upload_settings(analysis['id'], analysis_settings)
            st.rerun()
        except (JSONDecodeError, HTTPError) as e:
            st.error(f'Invalid Settings File: {e}')

@st.fragment
def set_analysis_settings(analysis):
    model_id = analysis['model']
    model = client.models.get(model_id).json()
    settings = client.models.settings.get(model_id).json()
    model_settings = settings["model_settings"]
    default_samples = settings.get("model_default_samples", 10)

    # Handle categorical settings
    valid_settings = [
        'event_set',
        'event_occurrence_id',
        'footprint_set',
        'vulnerability_set',
        'pla_loss_factor_set',
    ]

    def format_option(opt):
        return f'{opt["id"]} : {opt["desc"]}'

    def get_default_index(options, default=None):
        if default is None:
            return None
        return [i for i in range(len(options)) if options[i]['id'] == default][0]

    analysis_settings = {"model_supplier_id": model["supplier_id"],
                         "model_name_id": model["model_id"]}
    analysis_model_settings = {}
    for k, v in model_settings.items():
        if k in valid_settings:
            default = v.get('default', None)
            options = v['options']
            default_index = get_default_index(options, default)
            selected = st.selectbox(f"Set {v['name']}", options=v['options'], format_func=format_option, index=default_index)
            analysis_model_settings[k] = selected["id"]

    analysis_settings["model_settings"] = analysis_model_settings

    valid_outputs = ['gul', 'il', 'ri']
    if "valid_output_perspectives" in model_settings:
        valid_outputs = model_settings["valid_output_perspectives"]

    opt_cols = st.columns(5)
    with opt_cols[0]:
        gul_opt = st.checkbox("GUL", help="Ground up loss", value=True, disabled=("gul" not in valid_outputs))
    with opt_cols[1]:
        il_opt = st.checkbox("IL", help="Insured loss", disabled=("il" not in valid_outputs))
    with opt_cols[2]:
        ri_opt = st.checkbox("RI", help="Reinsurance net loss", disabled=("ri" not in valid_outputs))

    default_summary = {
        "aalcalc": True,
        "eltcalc": True,
        "id": 1,
        "lec_output": True,
        "leccalc": {
            "full_uncertainty_aep": True,
            "full_uncertainty_oep": True,
            "return_period_file": True
        }
    }

    analysis_settings["gul_output"] = gul_opt
    analysis_settings["gul_summaries"] = [default_summary,]
    analysis_settings["il_output"] = il_opt
    analysis_settings["il_summaries"] = [default_summary,]
    analysis_settings["ri_otuput"] = ri_opt
    analysis_settings["ri_summaries"] = [default_summary,]
    analysis_settings["number_of_samples"] = st.number_input("Number of samples",
                                                             min_value = 1,
                                                             value = default_samples)

    def get_oed_fields(analysis_id):
        oed_fields = client.analyses.input_file.get_dataframe(analysis_id)['account.csv'].columns.to_list()
        # oed_fields.append("AllRisks") # Is this options necessary?
        return oed_fields

    # TODO: Add these drill down options to analysis settings
    with st.expander("Drill-down options"):
        oed_fields = get_oed_fields(analysis["id"])

        if "num_summary_levels" not in st.session_state:
            st.session_state['num_summary_levels'] = 0
        for i in range(st.session_state.num_summary_levels):
            remove_button, multi_select = st.columns([1, 9])
            with remove_button:
                if st.button(":material/remove:", key=f"remove_summary_level_{i}"):
                    st.session_state.num_summary_levels -= 1
                    st.rerun(scope="fragment")
            with multi_select:
                st.multiselect("Summary Levels", key=f"summary_level_{i}",
                               options=oed_fields, label_visibility="collapsed")

        if st.button("Add Summary Level", icon=":material/add:"):
            st.session_state.num_summary_levels += 1
            st.rerun(scope="fragment")

    if st.button("Submit"):
        try:
            client.upload_settings(analysis['id'], analysis_settings)
            st.session_state.analysis_settings_submitted = True
        except (JSONDecodeError, HTTPError) as e:
            st.error(f'Invalid Settings File: {e}')
        st.rerun()

left, middle, right = st.columns(3)

# Settings buttons
disable_button = (selected is None or selected['status'] not in ['READY', 'NEW'])
if left.button("Upload Settings File", disabled=disable_button,
               use_container_width=True):
    upload_settings_file(selected)

disable_button = (selected is None or selected['status'] not in ['READY'])
if middle.button("Set Analysis Settings", disabled=disable_button,
                 use_container_width=True):
    set_analysis_settings(selected)


# Anlaysis run buttons
validation_list = [[validate_not_none, (selected,)],
               [validate_key_val, (selected, 'status', 'NEW')]]

validations = []
for validation in validation_list:
    vfunc, vargs = validation
    validations.append(vfunc(*vargs))
    if not validations[-1][0]:
        break

generateDisabled = True
if all([v[0] for v in validations]):
    generateDisabled = False

if left.button("Generate Inputs", use_container_width=True, disabled=generateDisabled):
    try:
        client.analyses.generate(selected['id'])
    except HTTPError as e:
        st.error(e)

validation_list = [[validate_not_none, (selected, 'Anlaysis row')],
                   [validate_key_val, (selected, 'status', 'READY')],
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

# TODO: Move the RUN / GENERATE INPUTS buttons to after analysis settings
