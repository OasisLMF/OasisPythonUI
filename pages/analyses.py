from oasis_data_manager.errors import OasisException
import streamlit as st
import pandas as pd
from requests.exceptions import HTTPError
from modules.client import ClientInterface
from modules.nav import SidebarNav
from modules.rerun import RefreshHandler
from modules.validation import KeyInValuesValidation, KeyNotNoneValidation, KeyValueValidation, NotNoneValidation, ValidationGroup
import json
from json import JSONDecodeError
import altair as alt
import time
from pages.components.create import create_analysis_form, create_portfolio_form, create_analysis_settings
from pages.components.display import DataframeView, MapView
import logging

from pages.components.process import enrich_analyses

logger = logging.getLogger(__name__)

st.set_page_config(
    page_title = "Analysis",
    layout = "centered"
)

SidebarNav()

##########################################################################################
# Header
##########################################################################################

cols = st.columns([0.1, 0.8, 0.1])
with cols[1]:
    st.image("images/oasis_logo.png")

# Retrieve client
if "client" in st.session_state:
    client = st.session_state.client
    client_interface = ClientInterface(client)
else:
    st.switch_page("app.py")

##########################################################################################
"## Portfolios"

show_portfolio_tab, create_portfolio_tab = st.tabs(['Show Portfolios', 'Create Portfolio'])

def show_portfolio():
    datetime_cols = ['created', 'modified']
    display_cols = [ 'id', 'name', 'created', 'modified', ]

    portfolios = client_interface.portfolios.get(df=True)
    portfolio_view = DataframeView(portfolios, display_cols=display_cols)
    portfolio_view.convert_datetime_cols(datetime_cols)
    portfolio_view.display()

def create_portfolio():
    form_data = create_portfolio_form()

    if form_data is None:
        return

    try:
        with st.spinner(text="Creating portfolio..."):
            client_interface.portfolios.create(name = form_data.get('name'),
                                               location_file = form_data.get('location_file'),
                                               accounts_file = form_data.get('accounts_file'),
                                               reinsurance_info_file = form_data.get('reinsurance_info_file'),
                                               reinsurance_scope_file = form_data.get('reinsurance_scope_file')
                                               )
        st.success("Successfully created portfolio")
        time.sleep(0.5)
        st.rerun()
    except HTTPError as e:
        st.error(e)


with show_portfolio_tab:
    show_portfolio()
with create_portfolio_tab:
    create_portfolio()

##########################################################################################
"## Analyses"

analysis_container = st.container()

rerun_interval_analysis = None

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

def analysis_summary_expander(selected):
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


def run_analysis(re_handler):
    analyses = client_interface.analyses.get(df=True)
    portfolios = client_interface.portfolios.get(df=True)
    models = client_interface.models.get(df=True)

    completed_statuses = ['RUN_COMPLETED', 'RUN_CANCELLED', 'RUN_ERROR']
    running_statuses = ['RUN_QUEUED', 'RUN_STARTED']

    re_handler.update_queue()

    # Check for running analysis
    running_analyses = analyses[analyses['status'].isin(running_statuses)]
    if not re_handler.is_refreshing() and not running_analyses.empty:
        for analysis_id in running_analyses['id']:
            re_handler.start(analysis_id, completed_statuses)

    left, middle, right = st.columns(3, vertical_alignment='center')
    st.write('1) Select an analysis:')

    portfolios = client_interface.portfolios.get(df=True)
    models = client_interface.models.get(df=True)
    analyses = enrich_analyses(analyses, portfolios, models).sort_values('id')

    display_cols = ['name', 'portfolio_name', 'model_id', 'model_supplier', 'status']

    analyses_view = DataframeView(analyses, selectable=True, display_cols=display_cols)
    selected = analyses_view.display()

    # Analysis run buttons
    validations = ValidationGroup()
    validations.add_validation(NotNoneValidation('Selected analysis'), selected)
    validations.add_validation(KeyInValuesValidation('Status'), selected,
                               'status', ['NEW', 'INPUTS_GENERATION_CANCELLED',
                                          'READY', 'RUN_COMPLETED',
                                          'RUN_CANCELLED', 'RUN_ERROR' ])


    left, middle, right = st.columns(3, vertical_alignment='center')
    left.markdown("2) Generate Inputs:")

    if middle.button("Generate", use_container_width=True, disabled=not validations.is_valid()):
        try:
            client.analyses.generate(selected['id'])
            st.session_state.rerun_analysis = True
            st.session_state.rerun_queue.append((selected['id'], 'READY'))
            st.rerun()
        except HTTPError as e:
            st.error(e)


    left, middle, right = st.columns(3, vertical_alignment='center')
    left.markdown("3) Setup Analysis:")

    # Upload settings button
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

    def set_analysis_settings(analysis):
        model = client.models.get(analysis['model']).json()
        model_settings = client.models.settings.get(analysis['model']).json()

        analysis_settings = create_analysis_settings(model, model_settings)

        if analysis_settings is not None:
            try:
                client.upload_settings(analysis['id'], analysis_settings)
            except (JSONDecodeError, HTTPError) as e:
                st.error(f'Invalid Settings File: {e}')
            st.rerun()

    validations = ValidationGroup()
    validations.add_validation(NotNoneValidation('Analysis'), selected)
    validations.add_validation(KeyInValuesValidation('Status'), selected, 'status', ['READY', 'NEW'])
    if middle.button("Upload Settings File", disabled=not validations.is_valid(),
                   use_container_width=True):
        upload_settings_file(selected)

    # Set settings button
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


    # Run analysis button
    left, middle, right = st.columns(3, vertical_alignment='center')
    left.markdown("4) Run Analysis:")

    validations = ValidationGroup()
    validations.add_validation(NotNoneValidation('Analysis'), selected)
    validations.add_validation(KeyInValuesValidation('Status'), selected,
                               'status', ['READY', 'RUN_COMPLETED',
                                          'RUN_CANCELLED', 'RUN_ERROR'])
    validations.add_validation(KeyNotNoneValidation('Settings'), selected, 'settings')

    run_enabled = validations.is_valid()
    msg = None
    if not run_enabled:
        msg = validations.message

    if middle.button("Run", use_container_width=True, disabled=not run_enabled, help=msg):
        try:
            client_interface.run(selected['id'])

            st.success("Run started")
            time.sleep(0.5)

            re_handler.start(selected['id'], completed_statuses)
        except HTTPError as e:
            st.error('Starting run failed.')
            logger.error(e)

    # Misc buttons
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


# Initialise refreshing
re_handler = RefreshHandler(client_interface)
run_every = re_handler.run_every()

@st.fragment(run_every=run_every)
def analysis_fragment():
    run_analysis_tab, create_analysis_tab = st.tabs(["Run Analysis", "Create Analysis"])
    with create_analysis_tab:
        new_analysis()

    with run_analysis_tab:
        run_analysis(re_handler)


analysis_fragment()
if run_every is not None:
    st.info('Analysis running.')
