from oasis_data_manager.errors import OasisException
from requests.exceptions import HTTPError
import streamlit as st
from modules.nav import SidebarNav
from modules.rerun import RefreshHandler
from modules.settings import get_analyses_settings
from pages.components.display import DataframeView, MapView
from pages.components.create import create_analysis_form
from modules.validation import KeyInValuesValidation, NotNoneValidation, ValidationError, ValidationGroup
import time
from json import JSONDecodeError

st.set_page_config(
    page_title = "Simplified Demo",
    layout = "centered"
)

SidebarNav()

"# OasisLMF UI - Simplified"

if "client" in st.session_state:
    client = st.session_state.client
    client_interface = st.session_state.client_interface
else:
    st.switch_page("app.py")

'## Create Analysis'

create_container = st.container(border=True)

'## Run Analysis'

run_container = st.container(border=True)

with create_container:
    '#### Portfolio Selection'

    datetime_cols = ['created', 'modified']
    display_cols = [ 'id', 'name', 'created', 'modified', ]

    portfolios = client_interface.portfolios.get(df=True)
    portfolio_view = DataframeView(portfolios, display_cols=display_cols, selectable=True)
    portfolio_view.convert_datetime_cols(datetime_cols)
    selected_portfolio = portfolio_view.display()

    '#### Model Selection'
    models = client_interface.models.get(df=True)
    display_cols = ['id', 'supplier_id', 'model_id', 'version_id', 'created', 'modified']
    datetime_cols = ['created', 'modified']

    model_view = DataframeView(models, selectable=True, display_cols=display_cols)
    model_view.convert_datetime_cols(datetime_cols)
    selected_model = model_view.display()

    validations = ValidationGroup()
    validations = validations.add_validation(NotNoneValidation("Portfolio"), selected_portfolio)
    validations = validations.add_validation(NotNoneValidation("Model"), selected_model)

    enable_popover = True
    msg = None
    try:
        validations.validate()
    except ValidationError as e:
        msg = e.message
        enable_popover = False

    # Set up row of buttons
    cols = st.columns([0.25, 0.25, 0.5])

    with cols[0]:
        with st.popover("Create Analysis", disabled=not enable_popover, help=msg, use_container_width=True):
            resp = create_analysis_form(portfolios=[selected_portfolio], models=[selected_model])
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
                     help=validation.message, use_container_width=True):
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

    if run_every is not None:
        st.write(f'Refreshing.')

    @st.fragment(run_every=run_every)
    def analysis_fragment():
        re_handler.update_queue()

        analyses = client_interface.analyses.get(df=True)
        valid_statuses = ['NEW', 'READY', 'RUN_QUEUED', 'RUN_STARTED', 'RUN_COMPLETED', 'RUN_CANCELLED', 'RUN_ERROR']
        analyses = analyses[analyses['status'].isin(valid_statuses)]
        display_cols = ['id', 'name', 'portfolio', 'model', 'modified', 'status']
        datetime_cols = ['modified']

        analyses_view = DataframeView(analyses, display_cols=display_cols, selectable=True)
        analyses_view.convert_datetime_cols(datetime_cols)
        selected = analyses_view.display()

        valid_statuses = ['NEW', 'READY', 'RUN_CANCELLED', 'RUN_ERROR']
        validations = ValidationGroup()
        validations.add_validation(NotNoneValidation('Analysis'), selected)
        validations.add_validation(KeyInValuesValidation('Status'), selected, 'status', valid_statuses)
        run_enabled = validations.is_valid()

        if st.button('Run', disabled = not run_enabled, help=validations.message):
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

    analysis_fragment()
