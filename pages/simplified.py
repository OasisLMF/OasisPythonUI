from oasis_data_manager.errors import OasisException
import tarfile
from io import BytesIO
from pathlib import Path
from requests.exceptions import HTTPError
import streamlit as st
from modules.nav import SidebarNav
from modules.rerun import RefreshHandler
from modules.settings import get_analyses_settings
from pages.components.display import DataframeView, MapView
from pages.components.create import create_analysis_form
from modules.validation import KeyInValuesValidation, NotNoneValidation, ValidationGroup
import time
from json import JSONDecodeError
from modules.client import ClientInterface

from pages.components.output import summarise_intputs
from pages.components.process import enrich_analyses, enrich_portfolios

st.set_page_config(
    page_title = "Simplified Demo",
    layout = "centered"
)

SidebarNav()

cols = st.columns([0.1, 0.8, 0.1])
with cols[1]:
    st.image("images/oasis_logo.png")

if "client" in st.session_state:
    client = st.session_state.client
    # client_interface = st.session_state.client_interface
    client_interface = ClientInterface(client)
else:
    st.switch_page("app.py")

'## Create Analysis'

if len(client_interface.portfolios.get()) == 0:
    st.error('No Portfolios Found')
    st.stop()
if len(client_interface.models.get()) == 0:
    st.error('No Models Found')
    st.stop()
create_container = st.container(border=True)

'## Run Analysis'

run_container = st.container(border=True)

with create_container:
    '#### Portfolio Selection'

    # Prepare portfolios data
    portfolios = client_interface.portfolios.get(df=True)
    portfolios = enrich_portfolios(portfolios, client_interface, disable=['acc'])

    display_cols = ['name', 'number_locations']

    portfolio_view = DataframeView(portfolios, display_cols=display_cols, selectable=True)
    selected_portfolio = portfolio_view.display()

    '#### Model Selection'
    models = client_interface.models.get(df=True)
    display_cols = [ 'model_id', 'supplier_id' ]

    model_view = DataframeView(models, selectable=True, display_cols=display_cols)
    selected_model = model_view.display()

    validations = ValidationGroup()
    validations = validations.add_validation(NotNoneValidation("Portfolio"), selected_portfolio)
    validations = validations.add_validation(NotNoneValidation("Model"), selected_model)

    enable_popover = validations.is_valid()
    msg = validations.get_message()

    # Set up row of buttons
    cols = st.columns([0.25, 0.25, 0.5])

    with cols[0]:
        with st.popover("Create Analysis", disabled=not enable_popover, help=msg,  use_container_width=True):
            if enable_popover:
                resp = create_analysis_form(portfolios=[selected_portfolio.to_dict()], models=[selected_model.to_dict()])
                if resp:
                    try:
                        with st.spinner("Generating analysis..."):
                            resp = client_interface.create_and_generate_analysis(resp['portfolio_id'], resp['model_id'], resp['name'])
                        st.success('Created analysis')
                        time.sleep(0.5)
                        st.rerun()
                    except OasisException as e:
                        st.error(e)

    with cols[1]:
        validation = NotNoneValidation("Portfolio")
        enable_map_button = validation.is_valid(selected_portfolio)

        if st.button("Exposure Map", disabled=not enable_map_button,
                     help=validation.get_message(), use_container_width=True):
            @st.dialog("Locations Map", width='large')
            def show_locations_map():
                with st.spinner('Loading map...'):
                    locations = client_interface.portfolios.endpoint.location_file.get_dataframe(selected_portfolio["id"])
                    exposure_map = MapView(locations)
                    exposure_map.display()
            show_locations_map()

with run_container:
    re_handler = RefreshHandler(client_interface)
    run_every = re_handler.run_every()

    @st.fragment(run_every=run_every)
    def analysis_fragment():
        re_handler.update_queue()

        analyses = client_interface.analyses.get(df=True)
        portfolios = client_interface.portfolios.get(df=True)
        models = client_interface.models.get(df=True)

        valid_statuses = ['NEW', 'READY', 'RUN_QUEUED', 'RUN_STARTED', 'RUN_COMPLETED', 'RUN_CANCELLED', 'RUN_ERROR']
        analyses = analyses[analyses['status'].isin(valid_statuses)]
        analyses = enrich_analyses(analyses, portfolios, models)

        display_cols = ['name', 'portfolio_name', 'model_id', 'model_supplier', 'status']

        analyses_view = DataframeView(analyses, display_cols=display_cols, selectable=True)
        selected = analyses_view.display()

        valid_statuses = ['NEW', 'READY', 'RUN_CANCELLED', 'RUN_ERROR']
        validations = ValidationGroup()
        validations.add_validation(NotNoneValidation('Analysis'), selected)
        validations.add_validation(KeyInValuesValidation('Status'), selected, 'status', valid_statuses)
        run_enabled = validations.is_valid()
        msg = validations.get_message()

        columns = st.columns([0.25, 0.25, 0.25, 0.25])

        with columns[0]:
            if st.button('Run', disabled = not run_enabled, help=msg, use_container_width=True):
                analysis_settings = get_analyses_settings(model_id = selected['model'])[0]

                try:
                    client_interface.upload_settings(selected['id'], analysis_settings)
                except (JSONDecodeError, HTTPError) as _:
                    st.error('Failed to upload settings')

                try:
                    if selected['status'] == 'NEW':
                        client_interface.generate_and_run(selected['id'])
                    else:
                        client_interface.run(selected['id'])

                    st.success("Run started.")
                    time.sleep(0.5)

                    re_handler.start(selected['id'], 'RUN_COMPLETED')
                except HTTPError as _:
                    st.error('Starting run Failed.')

        # Download button
        valid_statuses = ['RUN_COMPLETED']
        validations = ValidationGroup()
        validations.add_validation(NotNoneValidation('Analysis'), selected)
        validations.add_validation(KeyInValuesValidation('Status'), selected, 'status', valid_statuses)
        download_enabled = validations.is_valid()

        @st.dialog("Output", width="large")
        def display_outputs(ci, analysis_id):
            st.markdown('# Analysis Summary')
            locations = ci.analyses.get_file(analysis_id, 'input_file', df=True)['location.csv']
            a_settings = client.analyses.settings.get(analysis_id).json()
            summarise_intputs(locations, a_settings)


            st.markdown('# Results Summary')
            fname = f"analysis_{analysis_id}_output.tar.gz"
            fdata = ci.download_output(analysis_id)

            tdata = tarfile.open(fileobj=BytesIO(fdata))
            output_files = [m.name for m in tdata.getmembers() if m.isfile()]
            output_files = [Path(p).name for p in output_files]

            st.markdown(f"Output File Name: `{fname}`")

            st.download_button('Download Results File',
                               data=fdata,
                               file_name=fname)


        if download_enabled:
            with columns[1]:
                if st.button("Show Output", use_container_width=True):
                    display_outputs(client_interface, selected["id"])


    if len(client_interface.analyses.get()) == 0:
        st.error("No Analyses Found")
        st.stop()
    analysis_fragment()
    if run_every is not None:
        st.info(f'Analysis running.')
