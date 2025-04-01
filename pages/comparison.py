from modules.visualisation import OutputInterface
from pages.dashboard import get_analysis_outputs
import streamlit as st
import pandas as pd
from modules.nav import SidebarNav
from modules.client import ClientInterface
from modules.validation import LenValidation, NotNoneValidation, ValidationGroup
from pages.components.display import DataframeView
from pages.components.output import generate_aalcalc_comparison_fragment
from pages.components.output import generate_eltcalc_comparison_fragment

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

analyses = pd.DataFrame(analyses)
analyses = analyses[['name', 'id', 'portfolio', 'model']]
analyses = analyses.rename(columns={'id':'analysis_id'})

portfolios = client_interface.portfolios.get()
portfolios = pd.DataFrame(portfolios)[['id', 'name']]
portfolios = portfolios.rename(columns={'name': 'portfolio_name'})

models = client_interface.models.get()
models = pd.DataFrame(models)[['id', 'supplier_id', 'model_id']]

analyses = pd.merge(left=analyses, right=portfolios, how='left', left_on='portfolio', right_on='id')
analyses = pd.merge(left=analyses, right=models, how='left', left_on='model', right_on='id')
analyses = analyses[['analysis_id', 'name', 'portfolio_name', 'model_id', 'supplier_id']]

analyses_view = DataframeView(analyses, selectable='multi',
                              display_cols=['name', 'portfolio_name', 'model_id', 'supplier_id'])
selected = analyses_view.display()

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

settings1 = client.analyses.settings.get(selected['analysis_id'][0]).json()
settings2 = client.analyses.settings.get(selected['analysis_id'][1]).json()

perspectives = ['gul', 'il', 'ri']

for p in perspectives:
    if not settings1.get(f'{p}_output', False) and not settings2.get(f'{p}_output', False):
        continue

    st.write(f"## {p.upper()} Output")
    summaries1 = settings1.get(f'{p}_summaries', [{}])
    summaries2 = settings2.get(f'{p}_summaries', [{}])

    with st.spinner("Loading data..."):
        output_1 = get_analysis_outputs(selected['analysis_id'][0])
        output_2 = get_analysis_outputs(selected['analysis_id'][1])

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
            generate_eltcalc_comparison_fragment(p, output_1, output_2,
                                                 name_1=selected['name'][0],
                                                 name_2=selected['name'][1])
