from oasis_data_manager.errors import OasisException
import streamlit as st
import pandas as pd
from requests.exceptions import HTTPError
from modules.nav import SidebarNav
from modules.validation import KeyInValuesValidation, KeyNotNoneValidation, KeyValueValidation, NameValidation, NotNoneValidation, ValidationGroup
import os
import json
from json import JSONDecodeError
import pydeck as pdk
import altair as alt
import time
from pages.components.create import create_analysis_form
from pages.components.display import DataframeView, MapView

st.set_page_config(
    page_title = "Analysis",
    layout = "centered"
)

SidebarNav()

"# OasisLMF UI"

if st.button("♻️ "):
    st.rerun()

if "client" in st.session_state:
    client = st.session_state.client
    client_interface = st.session_state.client_interface
else:
    st.switch_page("app.py")

"## Portfolios"


show_portfolio, create_portfolio = st.tabs(['Show Portfolios', 'Create Portfolio'])

datetime_cols = ['created', 'modified']
display_cols = [ 'id', 'name', 'created', 'modified', ]
with show_portfolio:
    portfolios = client_interface.portfolios.get(df=True)
    portfolio_view = DataframeView(portfolios, display_cols=display_cols)
    portfolio_view.convert_datetime_cols(datetime_cols)
    portfolio_view.display()

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
        name = st.text_input('Portfolio Name', value=None, key='portfolio_name')
        loc_file = st.selectbox('Select Location File', options, index=None)
        acc_file = st.selectbox('Select Accounts File', options, index=None)
        ri_file = st.selectbox('Select Reinsurance Info File', options, index=None)
        rs_file = st.selectbox('Select Reinsurance Scope File', options, index=None)

        submitted = st.form_submit_button("Create Portfolio")

        if submitted:
            validation = NameValidation()
            if validation.is_valid(name):
                st.session_state.portfolio_form_data.update({
                    'name': name,
                    'location_file': loc_file,
                    'accounts_file': acc_file,
                    'reinsurance_info_file': ri_file,
                    'reinsurance_scope_file': rs_file,
                    'submitted': True
                })
            else:
                st.error(validation.message)
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
                with st.spinner(text="Creating portfolio..."):
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
                st.success("Successfully created portfolio")
                time.sleep(0.5)
                st.rerun()
            except HTTPError as e:
                st.error(e)

with create_portfolio:
    new_portfolio()

"## Analyses"

rerun_interval_analysis = None

def display_analyses(client_interface):
    analyses = client_interface.analyses.get(df=True)

    display_cols = [ 'id', 'name', 'portfolio', 'model', 'created', 'modified',
                    'status' ]
    datetime_cols = ['created', 'modified']

    '1) Select an analysis:'
    analyses_view = DataframeView(analyses, selectable=True, display_cols=display_cols)
    analyses_view.convert_datetime_cols(datetime_cols)
    selected = analyses_view.display()

    return selected


def display_select_models(models):
    st.write('Select Model')

    display_cols = ['id', 'supplier_id', 'model_id', 'version_id', 'created', 'modified']
    datetime_cols = ['created', 'modified']

    model_view = DataframeView(models, selectable=True, display_cols=display_cols)
    model_view.convert_datetime_cols(datetime_cols)
    selected = model_view.display()

    return selected


@st.fragment
def new_analysis():
    portfolios = client_interface.portfolios.get()
    models = client_interface.models.get()

    resp = create_analysis_form(portfolios, models)
    if resp:
        try:
            client_interface.create_analysis(resp['portfolio_id'], resp['model_id'], resp['name'])
            st.success('Created analysis')
            time.sleep(0.5)
            st.rerun()
        except OasisException as e:
            st.error(e)

# Tabs for show and create

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

    if os.path.exists('defaults/analysis_settings.json'):
        with open('defaults/analysis_settings.json', 'r') as f:
            analysis_settings = json.load(f)
    else:
        analysis_settings = {'model_settings': {}}
    analysis_settings["model_supplier_id"] = model["supplier_id"]
    analysis_settings["model_name_id"] = model["model_id"]
    for k, v in model_settings.items():
        if k in valid_settings:
            default = v.get('default', None)
            options = v['options']
            default_index = get_default_index(options, default)
            selected = st.selectbox(f"Set {v['name']}", options=v['options'], format_func=format_option, index=default_index)
            analysis_settings['model_settings'][k] = selected["id"]

    valid_outputs = ['gul', 'il', 'ri']
    if "valid_output_perspectives" in model_settings:
        valid_outputs = model_settings["valid_output_perspectives"]

    opt_cols = st.columns(5)
    with opt_cols[0]:
        gul_opt = st.checkbox("GUL", help="Ground up loss", value=True, disabled=("gul" not in valid_outputs))
        analysis_settings["gul_output"] = gul_opt
    with opt_cols[1]:
        il_opt = st.checkbox("IL", help="Insured loss", disabled=("il" not in valid_outputs))
        analysis_settings["il_output"] = il_opt
    with opt_cols[2]:
        ri_opt = st.checkbox("RI", help="Reinsurance net loss", disabled=("ri" not in valid_outputs))
        analysis_settings["ri_otuput"] = ri_opt

    analysis_settings["number_of_samples"] = st.number_input("Number of samples",
                                                             min_value = 1,
                                                             value = default_samples)

    if st.button("Submit"):
        try:
            client.upload_settings(analysis['id'], analysis_settings)
            st.session_state.analysis_settings_submitted = True
        except (JSONDecodeError, HTTPError) as e:
            st.error(f'Invalid Settings File: {e}')
        st.rerun()

@st.cache_data
def calculate_locations_success(locations, keys_df):
    num_locations = len(locations['loc_id'].unique())

    df = keys_df.groupby('PerilID')['LocID'].nunique()

    success_locations = df / num_locations
    success_locations = success_locations.rename("success_locations")
    success_locations = pd.DataFrame(success_locations.reset_index())
    return success_locations

@st.cache_data
def summarise_keys_generation(keys_df, locations):
    coverage_type_map = {
        1 : 'Building',
        2 : 'Other',
        3 : 'Contents',
        4 : 'BI',
    }

    locations = locations[['loc_id', 'BuildingTIV', 'OtherTIV', 'ContentsTIV', 'BITIV']]

    combineddf = keys_df[['LocID', 'PerilID', 'CoverageTypeID']]
    combineddf = combineddf.join(locations.set_index('loc_id'), on='LocID')

    coverage_tiv_map = {k: v + 'TIV' for k, v in coverage_type_map.items()}

    combineddf['CoverageTypeID_'] = combineddf['CoverageTypeID'].replace(coverage_tiv_map)
    def find_tiv(row):
        row['TIV'] = row[row['CoverageTypeID_']]
        return row

    combineddf = combineddf.apply(find_tiv, axis=1)
    combineddf = combineddf[['LocID', 'PerilID', 'CoverageTypeID', 'TIV']]
    groupeddf = combineddf.groupby(['PerilID', 'CoverageTypeID'])
    groupeddf_final = groupeddf.agg({"LocID" : "nunique", "TIV": "sum"})
    groupeddf_final = groupeddf_final.reset_index()
    groupeddf_final = groupeddf_final.replace(coverage_type_map)
    return groupeddf_final

@st.dialog("Locations Map", width='large')
def show_locations_map(locations):
    with st.spinner('Loading map...'):
        map_view = MapView(locations)
        map_view.display()


def analysis_summary_expander(selected):
    analysis_id = selected['id']
    with st.expander("Analysis Summary"):

        summary_tab, inputs_tab = st.tabs(["Summary", "Inputs"])

        input_files = client.analyses.input_file.get_dataframe(analysis_id)
        locations = input_files['location.csv']
        keys_df = input_files['keys.csv']

        if st.button("Show Locations Map"):
            show_locations_map(locations)

        success_locations = calculate_locations_success(locations, keys_df)

        bar_chart = alt.Chart(success_locations).mark_bar().encode(x='PerilID',
                                                                   y=alt.Y('success_locations').title('Percentage Success Locations'))

        keys_summary = summarise_keys_generation(keys_df, locations)
        column_config = {"LocID" : "No. Locations"}

        with summary_tab:
            '### Keys Summary'
            st.dataframe(keys_summary, hide_index=True, column_config=column_config, use_container_width=True)

            '### Keys Error'
            st.dataframe(input_files['keys-errors.csv'])

            st.altair_chart(bar_chart, use_container_width=True)

        @st.cache_data
        def convert_df(df):
            return df.to_csv().encode("utf-8")

        with inputs_tab:
            input_file_list = sorted(list(input_files.keys()))

            st.write("Input files:")
            for fname in input_file_list:

                left, right, _ = st.columns([1, 1, 1])
                left.write(fname)
                right.download_button("Download", convert_df(input_files[fname]),
                                      key=f'download_{fname}',
                                      file_name=fname)

if "rerun_analysis" not in st.session_state:
    st.session_state["rerun_analysis"] = False

if "rerun_queue" not in st.session_state:
    st.session_state["rerun_queue"] = []

run_every = None
if st.session_state.rerun_analysis:
    run_every = "5s"

def clear_rerun_queue(rerun_queue):
    while True:
        if len(rerun_queue) == 0:
            return []

        id, required_status = rerun_queue.pop(0)
        if not (client_interface.analyses.get(id)['status'] == required_status):
            rerun_queue.insert(0, (id, required_status))
            return rerun_queue

@st.fragment(run_every=run_every)
def analysis_fragment():
    # Handle rerun queue
    st.session_state.rerun_queue = clear_rerun_queue(st.session_state.rerun_queue)
    if len(st.session_state.rerun_queue) == 0 and st.session_state.rerun_analysis:
        st.session_state.rerun_analysis = False
        st.rerun()

    run_analyses, create_analysis = st.tabs(["Run Analysis", "Create Analysis"])
    with create_analysis:
        new_analysis()

    selected = None
    with run_analyses:
        selected = display_analyses(client_interface)


    with run_analyses:
        left, middle, right = st.columns(3, vertical_alignment='center')

    # Anlaysis run buttons
    validations = ValidationGroup()
    validations.add_validation(NotNoneValidation('Selected analysis'), selected)
    validations.add_validation(KeyValueValidation('Status'), selected, 'status', 'NEW')

    left.markdown("2) Generate Inputs:")
    if middle.button("Generate", use_container_width=True, disabled=not validations.is_valid()):
        try:
            client.analyses.generate(selected['id'])
            st.session_state.rerun_analysis = True
            st.session_state.rerun_queue.append((selected['id'], 'READY'))
            st.rerun()
        except HTTPError as e:
            st.error(e)

    # Settings buttons
    with run_analyses:
        left, middle, right = st.columns(3, vertical_alignment='center')

    left.markdown("3) Setup Analysis:")

    validations = ValidationGroup()
    validations.add_validation(NotNoneValidation('Analysis'), selected)
    validations.add_validation(KeyInValuesValidation('Status'), selected, 'status', ['READY', 'NEW'])
    if middle.button("Upload Settings File", disabled=not validations.is_valid(),
                   use_container_width=True):
        upload_settings_file(selected)

    validations = ValidationGroup()
    validations.add_validation(NotNoneValidation('Analysis'), selected)
    validations.add_validation(KeyValueValidation('Status'), selected, 'status', 'READY')
    enable_button = validations.is_valid()
    msg = None
    if not enable_button:
        msg = validations.message
    if right.button("Set Analysis Settings", disabled=not enable_button, help=msg,
                     use_container_width=True):
        set_analysis_settings(selected)


    validations = ValidationGroup()
    validations.add_validation(NotNoneValidation('Analysis'), selected)
    validations.add_validation(KeyValueValidation('Status'), selected, 'status', 'READY')
    validations.add_validation(KeyNotNoneValidation('Settings'), selected, 'settings')

    run_enabled = validations.is_valid()
    msg = None
    if not run_enabled:
        msg = validations.message

    with run_analyses:
        left, middle, right = st.columns(3, vertical_alignment='center')

    left.markdown("4) Run Analysis:")
    if middle.button("Run", use_container_width=True, disabled=not run_enabled, help=msg):
        try:
            client.analyses.run(selected['id'])
            st.session_state.rerun_analysis = True
            st.session_state.rerun_queue.append((selected['id'], 'RUN_COMPLETED'))
            st.rerun()
        except HTTPError as e:
            st.error(e)

    with run_analyses:
        left, middle, right = st.columns(3, vertical_alignment='center')

    validation = NotNoneValidation('Selected analysis')
    button_enabled = validation.is_valid(selected)

    if left.button("Delete", use_container_width=True, disabled = not button_enabled, help=validation.message):
        try:
            client.analyses.delete(selected['id'])
            st.rerun()
        except HTTPError as e:
            st.error(e)

    if selected is not None and selected['status'] in ['READY', 'RUN_COMPLETED']:
        analysis_summary_expander(selected)

analysis_fragment()
