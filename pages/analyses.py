from oasis_data_manager.errors import OasisException
import streamlit as st
from requests.exceptions import HTTPError
from modules.client import ClientInterface
from modules.nav import SidebarNav
from modules.rerun import RefreshHandler
from modules.validation import KeyInValuesValidation, KeyNotNoneValidation, KeyValueValidation, NotNoneValidation, ValidationGroup
import json
from json import JSONDecodeError
import time
from pages.components.create import create_analysis_form, create_portfolio_form, create_analysis_settings
from pages.components.display import DataframeView
import logging

from pages.components.logs import display_traceback_file
from pages.components.process import enrich_analyses
from pages.components.output import summarise_inputs

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

def show_portfolio():
    display_cols = [ 'name' ]

    portfolios = client_interface.portfolios.get(df=True)
    portfolio_view = DataframeView(portfolios, display_cols=display_cols)
    portfolio_view.display()

@st.dialog(title="Create Portfolio")
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

st.write("Available Portfolios: ")
show_portfolio()
if st.button("Create Portfolio"):
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
    analysis_id = selected['id']
    with st.expander("Analysis Summary"):

        summary_tab, inputs_tab, outputs_tab = st.tabs(["Summary", "Inputs", "Outputs"])

        @st.cache_data(show_spinner="Fetching input data...")
        def get_input_file(analysis_id):
            return client_interface.analyses.get_file(analysis_id, 'input_file', df=True)

        inputs = get_input_file(analysis_id)

        locations = inputs.get('location.csv', None)
        if client.analyses.get(analysis_id).json().get('settings') is not None:
            a_settings = client.analyses.settings.get(analysis_id).json()
        else:
            a_settings = None

        with summary_tab:
            summarise_inputs(locations, a_settings)

        @st.cache_data
        def convert_df(df):
            return df.to_csv().encode("utf-8")

        with inputs_tab:
            input_file_list = sorted(list(inputs.keys()))

            st.write("Input files:")
            for fname in input_file_list:

                left, right, _ = st.columns([1, 1, 1])
                left.write(fname)
                right.download_button("Download", convert_df(inputs[fname]),
                                      key=f'download_{fname}',
                                      file_name=fname)


        @st.cache_data(show_spinner="Fetching output data...")
        def get_output_file(analysis_id):
            return client_interface.analyses.get_file(analysis_id, 'output_file', df=True)

        if selected['status'] == 'RUN_COMPLETED':
            outputs = get_output_file(analysis_id)
            with outputs_tab:
                output_file_list = sorted(list(outputs.keys()))

                st.write("Output files:")
                for fname in output_file_list:

                    left, right, _ = st.columns([1, 1, 1])
                    left.write(fname)
                    right.download_button("Download", convert_df(outputs[fname]),
                                          key=f'download_{fname}',
                                          file_name=fname)

                fname = f"analysis_{analysis_id}_output.tar.gz"
                @st.cache_data(show_spinner="Fetching output tar data...")
                def get_output_tar(analysis_id):
                    return client_interface.download_output(analysis_id)
                fdata = get_output_tar(analysis_id)

                st.download_button('Download All Outputs',
                                   data=fdata,
                                   file_name=fname)
        else:
            outputs = None
            with outputs_tab:
                st.info("Run not complete.")


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
    analyses = enrich_analyses(analyses, portfolios, models).sort_values('id', ascending=False)

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
            st.success('Input generation started.')
            time.sleep(0.5)
            re_handler.start(selected['id'], ['READY', 'INPUTS_GENERATION_CANCELLED', 'INPUTS_GENERATION_ERROR'])
        except HTTPError as e:
            st.error("Input generation failed.")
            logger.error(e)


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
                st.success('Analysis settings uploaded.')
                time.sleep(0.5)
                st.rerun()
            except (JSONDecodeError, HTTPError) as e:
                st.error(f'Invalid Settings File: {e}')
                logger.error(e)

    @st.dialog("Set analysis settings")
    def set_analysis_settings(analysis):
        model = client.models.get(analysis['model']).json()
        model_settings = client.models.settings.get(analysis['model']).json()

        valid_oed_fields = client.analyses.summary_levels_file.get(analysis['id']).json()
        invalid_fields = ['OEDVersion']

        keys = list(valid_oed_fields.keys())
        for k in keys:
            new_k = k.lower()
            valid_oed_fields[new_k] = valid_oed_fields.pop(k)['available']
            for f in invalid_fields:
                valid_oed_fields[new_k].pop(f, None)

        analysis_settings = create_analysis_settings(model, model_settings, oed_fields=valid_oed_fields)

        if analysis_settings is not None:
            try:
                client.upload_settings(analysis['id'], analysis_settings)
                st.success('Analysis settings uploaded.')
                time.sleep(0.5)
                st.rerun()
            except (JSONDecodeError, HTTPError) as e:
                st.error(f'Invalid Settings File: {e}')
                logger.error(e)

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
            st.error("Deletion failed.")
            logger.error(e)

    validations = ValidationGroup()
    validations.add_validation(NotNoneValidation('Analysis'), selected)

    run_enabled = validations.is_valid()
    msg = None
    if not run_enabled:
        msg = validations.message

    if middle.button("Logs", use_container_width=True, disabled=not run_enabled, help=msg):
        @st.dialog("Log", width='large')
        def error_log_dialog(analysis_id):
            input_gen_traceback = client_interface.analyses.get_traceback(analysis_id, 'input_generation')
            run_traceback = client_interface.analyses.get_traceback(analysis_id, 'run')

            if input_gen_traceback is not None:
                display_traceback_file(input_gen_traceback, trace_type='input_generation')

            if input_gen_traceback and run_traceback:
                st.write('---')

            if run_traceback is not None:
                display_traceback_file(run_traceback, trace_type='run')

            if input_gen_traceback is None and run_traceback is None:
                st.info('No traceback logs to show.')

        error_log_dialog(selected['id'])


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
