import streamlit as st
import pandas as pd
from requests.exceptions import HTTPError
from modules.nav import SidebarNav
from modules.validation import validate_name, validate_not_none, validate_key_vals, validate_key_is_not_null
from modules.client import check_analysis_status
import os
import json
from json import JSONDecodeError
import pydeck as pdk
import altair as alt
import time

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

if "client" in st.session_state:
    client = st.session_state.client
else:
    st.switch_page("app.py")


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
        name = st.text_input('Portfolio Name', value=None, key='portfolio_name')
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

def display_analyses(client):
    analyses = client.analyses.get().json()
    analyses = pd.json_normalize(analyses)

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

    '1) Select an analysis:'
    selected = st.dataframe(analyses, hide_index=True,
                                     column_config=column_config,
                                     column_order=display_cols,
                                     use_container_width=True,
                                     selection_mode="single-row",
                                     on_select="rerun",
                            )
    selected =  selected_to_row(selected, analyses)

    return selected


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
                st.success("Analysis created")
                time.sleep(0.5) # Briefly display the message
                st.rerun()
            else:
                for v in validations:
                    if v[0] is False:
                        st.error(v[1])
                submitted = False

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

def generate_location_map(locations):
    layer = pdk.Layer(
        'ScatterplotLayer',
        locations,
        get_position=["Longitude", "Latitude"],
        get_line_color = [0, 0, 0],
        get_fill_color = [255, 140, 0],
        radius_min_pixels = 1,
        radius_max_pixels = 50,
        radius_scale = 2,
        pickable=True,
        stroked=True,
        get_line_width=0.5,
    )

    viewstate = pdk.data_utils.compute_view(locations[['Longitude', 'Latitude']])

    # Prevent over zooming
    if viewstate.zoom > 18:
        viewstate.zoom = 18

    deck = pdk.Deck(layers=[layer], initial_view_state=viewstate,
                    tooltip={"text": "Peril: {LocPerilsCovered}\nBuilding TIV: {BuildingTIV}"},
                    map_style='light')

    return deck

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
        deck = generate_location_map(locations)
        st.pydeck_chart(deck, use_container_width=True)


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
        if not check_analysis_status(client, id, required_status):
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
        selected = display_analyses(client)


    with run_analyses:
        left, middle, right = st.columns(3, vertical_alignment='center')

    # Anlaysis run buttons
    validation_list = [[validate_not_none, (selected,)],
                   [validate_key_vals, (selected, 'status', ['NEW'])]]

    validations = []
    for validation in validation_list:
        vfunc, vargs = validation
        validations.append(vfunc(*vargs))
        if not validations[-1][0]:
            break

    generateDisabled = True
    if all([v[0] for v in validations]):
        generateDisabled = False

    left.markdown("2) Generate Inputs:")
    if middle.button("Generate", use_container_width=True, disabled=generateDisabled):
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
    disable_button = (selected is None or selected['status'] not in ['READY', 'NEW'])
    if middle.button("Upload Settings File", disabled=disable_button,
                   use_container_width=True):
        upload_settings_file(selected)

    enable_button, message = validate_key_vals(selected, 'status', ['READY'])
    if right.button("Set Analysis Settings", disabled=not enable_button, help=message,
                     use_container_width=True):
        set_analysis_settings(selected)



    validation_list = [[validate_not_none, (selected, 'Anlaysis row')],
                       [validate_key_vals, (selected, 'status', ['READY'])],
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

    with run_analyses:
        left, middle, right = st.columns(3, vertical_alignment='center')

    left.markdown("4) Run Analysis:")
    if middle.button("Run", use_container_width=True, disabled=runDisabled, help=help):
        try:
            client.analyses.run(selected['id'])
            st.session_state.rerun_analysis = True
            st.session_state.rerun_queue.append((selected['id'], 'RUN_COMPLETED'))
            st.rerun()
        except HTTPError as e:
            st.error(e)

    with run_analyses:
        left, middle, right = st.columns(3, vertical_alignment='center')

    buttonEnabled, _ = validate_not_none(selected)
    if left.button("Delete", use_container_width=True, disabled = not buttonEnabled):
        try:
            client.analyses.delete(selected['id'])
            st.rerun()
        except HTTPError as e:
            st.error(e)

    show_summary, _ = validate_key_vals(selected, 'status', ['READY', 'RUN_COMPLETED'])

    if show_summary:
        analysis_summary_expander(selected)

analysis_fragment()
