from modules.visualisation import OutputInterface
from pages.dashboard import get_analysis_outputs
import streamlit as st
import pandas as pd
from modules.nav import SidebarNav
from modules.client import ClientInterface
from modules.validation import LenValidation, NotNoneValidation, ValidationGroup
from pages.components.display import DataframeView
from pages.components.output import generate_aalcalc_comparison_fragment, generate_leccalc_comparison_fragment
from pages.components.output import generate_eltcalc_comparison_fragment, summarise_inputs

st.set_page_config(
    page_title = "Comparison",
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
    st.stop()

selected = pd.DataFrame(selected)

analysis_id_1 = selected['id'][0]
analysis_id_2 = selected['id'][1]

st.write("# Analysis Summary")
expander = st.expander('Analysis Summary')
with expander:
    cols = st.columns(2)
@st.cache_data
def get_analysis_inputs(ID):
    return client_interface.analyses.get_file(ID, 'input_file', df=True)

with cols[0]:
    st.write(f"## {selected['name'][0]}")
    with st.spinner("Loading data..."):
        inputs = get_analysis_inputs(analysis_id_1)
        settings1 = client.analyses.settings.get(analysis_id_1).json()

    with st.spinner('Loading analysis summary...'):
        summarise_inputs(inputs.get('location.csv', None), settings1, title_prefix='###')

with cols[1]:
    st.write(f"## {selected['name'][1]}")
    with st.spinner("Loading data..."):
        inputs = get_analysis_inputs(analysis_id_2)
        settings2 = client.analyses.settings.get(analysis_id_2).json()

    with st.spinner('Loading analysis summary...'):
        summarise_inputs(inputs.get('location.csv', None), settings2, title_prefix='###')

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

st.write("# Outputs")
for p in perspectives:
    if not settings1.get(f'{p}_output', False) and not settings2.get(f'{p}_output', False):
        continue

    st.write(f"## {p.upper()} Output")
    summaries1 = settings1.get(f'{p}_summaries', [{}])
    summaries2 = settings2.get(f'{p}_summaries', [{}])

    with st.spinner("Loading data..."):
        output_1 = get_analysis_outputs(analysis_id_1)
        output_2 = get_analysis_outputs(analysis_id_2)

    output_1 = OutputInterface(output_1)
    output_2 = OutputInterface(output_2)

    oed_field_1 = summaries1[0].get('oed_fields', None)
    if oed_field_1:
        output_1.set_oed_fields(p, oed_field_1)

    oed_field_2 = summaries2[0].get('oed_fields', None)
    if oed_field_2:
        output_2.set_oed_fields(p, oed_field_2)

    if summaries1[0].get('aalcalc', False) and summaries2[0].get('aalcalc', False):
        expander = st.expander("AAL Output")
        with expander:
            generate_aalcalc_comparison_fragment(p, output_1, output_2,
                                                 name_1=selected['name'][0],
                                                 name_2=selected['name'][1])

    if summaries1[0].get('eltcalc', False) and summaries2[0].get('eltcalc', False):
        expander = st.expander("ELT Output")
        with expander:
            locations_1 = get_locations_file(analysis_id_1)
            locations_2 = get_locations_file(analysis_id_2)

            locations = merge_locations(locations_1, locations_2)

            generate_eltcalc_comparison_fragment(p, output_1, output_2,
                                                 name_1=selected['name'][0],
                                                 name_2=selected['name'][1],
                                                 locations=locations)

    if summaries1[0].get('lec_output', False) and summaries2[0].get('lec_output', False):
        expander = st.expander("LEC Output")
        with expander:
            lec_outputs_1 = summaries1[0].get('leccalc', {})
            lec_outputs_2 = summaries2[0].get('leccalc', {})
            lec_outputs = {}
            for k, v in lec_outputs_1.items():
                if v and lec_outputs_2.get(k, False):
                    lec_outputs[k] = v
            generate_leccalc_comparison_fragment(p, [output_1, output_2], lec_outputs,
                                                 names=selected['name'].tolist())
