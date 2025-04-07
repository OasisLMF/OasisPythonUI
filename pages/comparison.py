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

analysis_ids = [selected['id'][i] for i in range(2)]

st.write("# Analysis Summary")
expander = st.expander('Analysis Summary')
with expander:
    cols = st.columns(2)
@st.cache_data
def get_analysis_inputs(ID):
    return client_interface.analyses.get_file(ID, 'input_file', df=True)

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

st.write("# Outputs")
for p in perspectives:
    if not all([s.get(f'{p}_output', False) for s in settings]):
        continue

    summaries = [s.get(f'{p}_summaries', [{}])[0] for s in settings]
    names = selected['name'].tolist()

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
        expander = st.expander("AAL Output")
        with expander:
            generate_aalcalc_comparison_fragment(p, outputs, names)

    if all([s.get('eltcalc', False) for s in summaries]):
        expander = st.expander("ELT Output")
        with expander:
            locations = [get_locations_file(id) for id in analysis_ids]
            locations = merge_locations(*locations)

            generate_eltcalc_comparison_fragment(p, outputs, names=names,
                                                 locations=locations)

    if all([s.get('lec_output', False) for s in summaries]):
        expander = st.expander("LEC Output")
        with expander:
            lec_outputs_list = [s.get('leccalc', {}) for s in summaries]
            lec_outputs = {}
            keys = lec_outputs_list[0].keys()
            for k in keys:
                if all([lec.get(k, False) for lec in lec_outputs_list]):
                    lec_outputs[k] = True
            generate_leccalc_comparison_fragment(p, outputs, lec_outputs,
                                                 names=names)
