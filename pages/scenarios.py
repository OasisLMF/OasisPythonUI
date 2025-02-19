from os.path import isfile
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
from modules.validation import KeyInValuesValidation, NotNoneValidation, ValidationGroup, IsNoneValidation
from modules.visualisation import OutputVisualisationInterface
import time
from json import JSONDecodeError
import json
from modules.client import ClientInterface
import logging

from pages.components.output import model_summary, summarise_intputs
from pages.components.process import enrich_analyses, enrich_portfolios

logger = logging.getLogger(__name__)

if isfile("ui-config.json"):
    with open("ui-config.json") as f:
        ui_config = json.load(f)
else:
    ui_config = {}

st.set_page_config(
    page_title = "Scenarios",
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
    model_map = ui_config.get("model_map", {})

    '#### Model Selection'
    models = client_interface.models.get(df=True)
    display_cols = [ 'model_id', 'supplier_id' ]

    model_view = DataframeView(models, selectable=True, display_cols=display_cols)
    selected_model = model_view.display()

    '#### Portfolio Selection'
    # Prepare portfolios data
    portfolios = client_interface.portfolios.get(df=True)

    # Find the corresponding portfolios
    def filter_valid_rows(df, key, valid_map, filter_col):
        if key is None:
            return df

        if type(key) is not str:
            key = str(key)

        valid_elements = valid_map.get(key, None)

        if valid_elements is None:
            return df

        _df = df.loc[df[filter_col].isin(valid_elements)]
        return _df

    selected_model_id = selected_model['model_id'] if selected_model is not None else None
    if selected_model_id:
        portfolios = filter_valid_rows(portfolios, selected_model_id, model_map, "name")
        portfolios = enrich_portfolios(portfolios, client_interface, disable=['acc'])

        display_cols = ['name', 'number_locations']

        portfolio_view = DataframeView(portfolios, display_cols=display_cols, selectable=True)
        selected_portfolio = portfolio_view.display()
    else:
        st.info("Please select a model.")
        selected_portfolio = None

    validations = ValidationGroup()
    validations = validations.add_validation(NotNoneValidation("Portfolio"), selected_portfolio)
    validations = validations.add_validation(NotNoneValidation("Model"), selected_model)

    enable_popover = validations.is_valid()
    msg = validations.get_message()

    # Set up row of buttons
    cols = st.columns([0.25, 0.25, 0.25, 0.25])

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
                    cols = locations.columns
                    if 'Latitude' not in cols or 'Longitude' not in cols:
                        st.error('Longitude and Latitude columns not found.')
                    else:
                        exposure_map = MapView(locations)
                        exposure_map.display()
            show_locations_map()

    with cols[2]:
        validation = NotNoneValidation("Model")
        enable_model_details = validation.is_valid(selected_model)

        if st.button("Model Details", disabled=not enable_model_details,
                     help = validation.get_message(), use_container_width=True):
            try:
                model_settings = client_interface.client.models.settings.get(selected_model['id']).json()
            except HTTPError as e:
                logger.error(e)
                model_settings = {}
            @st.dialog("Model Details", width="large")
            def model_details_dialog():
                model_summary(selected_model, model_settings, detail_level="full")
            model_details_dialog()

with run_container:
    re_handler = RefreshHandler(client_interface)
    run_every = re_handler.run_every()

    @st.fragment(run_every=run_every)
    def analysis_fragment():
        re_handler.update_queue()

        analyses = client_interface.analyses.get(df=True)
        portfolios = client_interface.portfolios.get(df=True)
        models = client_interface.models.get(df=True)

        completed_statuses = ['RUN_COMPLETED', 'RUN_CANCELLED', 'RUN_ERROR']
        running_statuses = ['RUN_QUEUED', 'RUN_STARTED']

        running_analyses = analyses[analyses['status'].isin(running_statuses)]
        if not re_handler.is_refreshing() and not running_analyses.empty:
            for analysis_id in running_analyses['id']:
                re_handler.start(analysis_id, completed_statuses)

        valid_statuses = ['NEW', 'READY', 'RUN_QUEUED', 'RUN_STARTED', 'RUN_COMPLETED', 'RUN_CANCELLED', 'RUN_ERROR']
        analyses = analyses[analyses['status'].isin(valid_statuses)]
        analyses = enrich_analyses(analyses, portfolios, models)

        display_cols = ['name', 'portfolio_name', 'model_id', 'model_supplier', 'status']

        analyses_view = DataframeView(analyses, display_cols=display_cols, selectable=True)
        selected = analyses_view.display()

        oed_group = st.pills("Group output by:",
                             [ "Portfolio", "Country", "Location"], selection_mode="multi")

        group_to_code = {
            'Portfolio': 'PortNumber',
            'Country': 'CountryCode',
            'Location': 'LocNumber'
        }

        valid_statuses = ['NEW', 'READY', 'RUN_CANCELLED', 'RUN_ERROR']
        validations = ValidationGroup()
        validations.add_validation(NotNoneValidation('Analysis'), selected)
        validations.add_validation(KeyInValuesValidation('Status'), selected, 'status', valid_statuses)
        val = IsNoneValidation()
        val.set_message('Analysis already running')
        validations.add_validation(val, run_every)

        run_enabled = validations.is_valid()
        msg = validations.get_message()

        columns = st.columns([0.25, 0.25, 0.25, 0.25])

        with columns[0]:
            if st.button('Run', disabled = not run_enabled, help=msg, use_container_width=True):
                model_id = client_interface.models.get(selected['model'])['model_id']
                analysis_settings = get_analyses_settings(model_name_id = model_id)[0]
                with open(analysis_settings, 'r') as f:
                    analysis_settings = json.load(f)
                if len(oed_group) > 0:
                    oed_group_codes = [group_to_code[g] for g in oed_group]
                    if analysis_settings.get('gul_output', False):
                        analysis_settings['gul_summaries'][0]['oed_fields'] = oed_group_codes
                    if analysis_settings.get('il_output', False):
                        analysis_settings['il_summaries'][0]['oed_fields'] = oed_group_codes
                    if analysis_settings.get('ri_output', False):
                        analysis_settings['il_summaries'][0]['oed_fields'] = oed_group_codes

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

                    re_handler.start(selected['id'], completed_statuses)
                except HTTPError as _:
                    st.error('Starting run failed.')

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

            # Graphs from output

            results_dict = ci.analyses.get_file(analysis_id, 'output_file', df=True)
            vis_interface = OutputVisualisationInterface(results_dict)

            def generate_perspective_visualisation(perspective, summaries_settings):
                if summaries_settings[0].get('eltcalc'):
                    st.write("### ELT Output")
                    eltcalc_df = vis_interface.get(summary_level=1, perspective=perspective, output_type='eltcalc')
                    eltcalc_df = DataframeView(eltcalc_df)
                    eltcalc_df.column_config['mean'] = st.column_config.NumberColumn('Mean', format='%.2f')
                    eltcalc_df.display()
                if summaries_settings[0].get('aalcalc'):
                    st.write("### AAL Output")
                    aal_fig = vis_interface.get(summary_level=1, perspective=perspective, output_type='aalcalc')
                    st.plotly_chart(aal_fig, use_container_width=True)
                if summaries_settings[0].get('lec_output'):
                    st.write("### LEC Output")
                    analysis_types = ["full_uncertainty", "wheatsheaf", "wheatsheaf_mean", "sample_mean"]
                    loss_types = ["aep", "oep"]
                    for a_type in analysis_types:
                        for l_type in loss_types:
                            param_name = f"{a_type}_{l_type}"
                            if summaries_settings[0].get("leccalc").get(param_name):
                                lec_fig = vis_interface.get(summary_level=1, perspective=perspective,
                                                            output_type='leccalc',
                                                            opts={'analysis_type': a_type,
                                                                  'loss_type': l_type})
                                st.plotly_chart(lec_fig, use_container_width=True)
                if summaries_settings[0].get('pltcalc'):
                    st.write("### PLT Output")
                    plt_fig = vis_interface.get(summary_level=1, perspective=perspective, output_type='pltcalc')
                    st.plotly_chart(plt_fig, use_container_width=True)

            if a_settings['gul_output']:
                st.write("## Ground Up Loss")
                generate_perspective_visualisation('gul', a_settings['gul_summaries'])

            if a_settings.get('il_output', False):
                st.write("## Insured Loss")
                generate_perspective_visualisation('il', a_settings['il_summaries'])

            if a_settings.get('ri_output', False):
                st.write("## Loss Net of Reinsurance")
                generate_perspective_visualisation('ri', a_settings['ri_summaries'])

            fname = f"analysis_{analysis_id}_output.tar.gz"
            st.markdown(f"Output File Name: `{fname}`")
            fdata = ci.download_output(analysis_id)

            tdata = tarfile.open(fileobj=BytesIO(fdata))
            output_files = [m.name for m in tdata.getmembers() if m.isfile()]
            output_files = [Path(p).name for p in output_files]

            st.download_button('Download Results File',
                               data=fdata,
                               file_name=fname)


        with columns[1]:
            if st.button("Show Output", use_container_width=True, disabled = not download_enabled):
                display_outputs(client_interface, selected["id"])


    if len(client_interface.analyses.get()) == 0:
        st.error("No analyses found.")
        st.stop()
    analysis_fragment()
    if run_every is not None:
        st.info('Analysis running.')
