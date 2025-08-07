from modules.authorisation import validate_page, handle_login
from modules.visualisation import OutputInterface
import streamlit as st
import pandas as pd
from modules.nav import SidebarNav
from modules.config import retrieve_ui_config
from modules.validation import LenValidation, NotNoneValidation, ValidationGroup
from pages.components.display import DataframeView
from pages.components.footer import generate_footer
from pages.components.output import generate_aalcalc_comparison_fragment, generate_leccalc_comparison_fragment
from pages.components.output import generate_eltcalc_comparison_fragment, summarise_inputs

##########################################################################################
# Header
##########################################################################################

ui_config = retrieve_ui_config()
validate_page("Comparison")

st.set_page_config(
    page_title = "Comparison",
    layout = "centered"
)

cols = st.columns([0.1, 0.8, 0.1])
with cols[1]:
    st.image("images/oasis_logo.png")

##########################################################################################
# Page
##########################################################################################

# Retrieve client
handle_login(ui_config.skip_login)

SidebarNav()

client_interface = st.session_state["client_interface"]
client = client_interface.client

'## Compare two scenario loss estimates'
'This tool enables two analyses to be compared to look at the difference in, for example - change in exposure, hazard or vulnerability.'
'A use case for this, would be to compare loss from flood in an area defended by a different level of flood protection, or no flood protection.'
'It can also be used to test the impact of two different hazard scenarios, different vulnerability of the buildings in the portfolio, or of a different value/number of buildings in that portfolio.'

"First, select two analyses, from the precomputed set. To add an analysis to the list, run it in the 'Scenario' tool."
'Currently, it is not possible to add your own scenarios directly; please describe any scenario you would like to add, here: https://github.com/OasisLMF/OasisPythonUI/issues'


analyses = sorted(client_interface.analyses.search(metadata={'status': 'RUN_COMPLETED'}), key=lambda x: x['id'], reverse=True)
cols = st.columns(2)
selected = []
with cols[0]:
    selected_analysis = st.selectbox("Select Analysis 1", options=analyses,
                            format_func= lambda x : x['name'], index=None)
    if selected_analysis:
        selected.append(selected_analysis)
with cols[1]:
    selected_analysis = st.selectbox("Select Analysis 2", options=analyses,
                            format_func= lambda x : x['name'], index=None)
    if selected_analysis:
        selected.append(selected_analysis)


validations = ValidationGroup()
none_validation = NotNoneValidation()
none_validation.message = 'Select 2 analyses.'
validations.add_validation(none_validation, selected)
len_validation = LenValidation()
len_validation.message = 'Select 2 analyses.'
validations.add_validation(len_validation, selected, 2)

if not validations.is_valid():
    st.info(validations.message)
    generate_footer(ui_config)
    st.stop()

selected = pd.DataFrame(selected)

analysis_ids = [selected['id'][i] for i in range(2)]

st.subheader("Analysis Summary")
st.markdown("""
This section summarises the analyses selected for comparison: the number and value of buildings in the portfolio;
the hazard footprint selected, and the outputs available.
Under 'output settings', 'gul' referes to ground up loss, before insurance contract terms apply; 'aalcal' denotes that the
Annual Average Loss has been estimated; 'eltcalc' denotes that the per-event loss has been estimated.
""")

expander = st.expander('Analysis Summary')
with expander:
    cols = st.columns(2)
@st.cache_data
def get_analysis_inputs(ID):
    return client_interface.analyses.get_file(ID, 'input_file', df=True)

@st.cache_data
def get_analysis_outputs(ID):
    return client_interface.analyses.get_file(ID, 'output_file', df=True)

settings = []
with cols[0]:
    st.write(f"## {selected['name'][0]}")
    with st.spinner("Loading data..."):
        inputs = get_analysis_inputs(analysis_ids[0])
        settings.append(client.analyses.settings.get(analysis_ids[0]).json())

    with st.spinner('Loading analysis summary...'):
        summarise_inputs(inputs.get('location.csv', None), settings[0], title_prefix='###')

with cols[1]:
    st.write(f"## {selected['name'][1]}")
    with st.spinner("Loading data..."):
        inputs = get_analysis_inputs(analysis_ids[1])
        settings.append(client.analyses.settings.get(analysis_ids[1]).json())

    with st.spinner('Loading analysis summary...'):
        summarise_inputs(inputs.get('location.csv', None), settings[1], title_prefix='###')

@st.cache_data
def get_locations_file(ID):
    inputs = client_interface.analyses.get_file(ID, 'input_file', df=True)
    if inputs:
        return inputs.get('location.csv')
    return None

@st.cache_data
def merge_locations(locations_1, locations_2):
    if locations_1 is None or locations_2 is None:
        return None
    locations_1 = locations_1[['LocNumber', 'Longitude', 'Latitude']]
    locations_2 = locations_2[['LocNumber', 'Longitude', 'Latitude']]

    locations = pd.merge(left=locations_1, right=locations_2, how='outer',
                         on='LocNumber', suffixes=('_left', '_right'))
    locations['Latitude'] = locations[['Latitude_left', 'Latitude_right']].mean(axis=1)
    locations['Longitude'] = locations[['Longitude_left', 'Longitude_right']].mean(axis=1)
    locations = locations[['LocNumber', 'Latitude', 'Longitude']]
    return locations

perspectives = ['gul', 'il', 'ri']

st.write("# Loss estimates")
'This section enables comparison of the scenario loss from each of the analyses.'

for p in perspectives:
    if not all([s.get(f'{p}_output', False) for s in settings]):
        continue

    summaries = [s.get(f'{p}_summaries', [{}])[0] for s in settings]
    names = selected['name'].tolist() # 'GUL OUTPUT' SHOULD BE MORE UNDERSTANDABLE FOR NON-EXPERT USERS BY USING TITLE 'GROUND UP LOSS'

    supported_outputs = ['aalcalc', 'eltcalc', 'lec_output']
    no_outputs = True
    for output in supported_outputs:
        if all([s.get(output, False) for s in summaries]):
            st.write(f"## {p.upper()} Output")
            no_outputs = False
            break

    if no_outputs:
        st.error('No comparison available.')

    with st.spinner("Loading data..."):
        outputs = [OutputInterface(get_analysis_outputs(id)) for id in analysis_ids]

    for output, s in zip(outputs, summaries):
        oed_fields = s.get('oed_fields', None)
        if oed_fields is not None:
            output.set_oed_fields(p, oed_fields)

    if all([s.get('aalcalc', False) for s in summaries]):
        st.write("### Mean loss comparison chart")
        generate_aalcalc_comparison_fragment(p, outputs, names)

    if all([s.get('eltcalc', False) for s in summaries]):
        st.write("### Per-location loss estimates")
        locations = [get_locations_file(id) for id in analysis_ids]
        locations = merge_locations(*locations)

        generate_eltcalc_comparison_fragment(p, outputs, names=names,
                                             locations=locations)

    if all([s.get('lec_output', False) for s in summaries]):
        st.write("### LEC Output")
        lec_outputs_list = [s.get('leccalc', {}) for s in summaries]
        lec_outputs = {}
        keys = lec_outputs_list[0].keys()
        for k in keys:
            if all([lec.get(k, False) for lec in lec_outputs_list]):
                lec_outputs[k] = True
        generate_leccalc_comparison_fragment(p, outputs, lec_outputs,
                                             names=names)

generate_footer(ui_config)
