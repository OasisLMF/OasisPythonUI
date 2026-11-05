"""Compare: results of two runs side by side (showcase runs and your own runs)."""
import pandas as pd
import streamlit as st

from modules.scenarios import display_name, showcase_analyses, visitor_analyses
from modules.visualisation import OutputInterface
from pages.components.common import PERSPECTIVES_MAP
from pages.components.output import (EP_CALC_LABELS, generate_aalcalc_comparison_fragment,
                                     generate_alt_comparison_fragment, generate_eltcalc_comparison_fragment,
                                     generate_leccalc_comparison_fragment, generate_pltcalc_comparison_fragment,
                                     summarise_inputs)
from scenarios_ui.common import Context, footer

ctx = Context()
ui_config = ctx.ui_config
client_interface = ctx.ci
client = client_interface.client

st.title('Compare')
st.markdown(
    'Compare the results of two runs side by side: for example a flood with and without defences, two '
    'different scenarios, or the same scenario with different settings. Choose from the showcase runs and '
    'your own completed runs.')

all_analyses = client_interface.analyses.get()
showcase = {a['id'] for a in showcase_analyses(all_analyses, ctx.limits)}
mine = {a['id'] for a in visitor_analyses(all_analyses, ctx.vid)}
analyses = sorted([a for a in all_analyses if a['status'] == 'RUN_COMPLETED' and a['id'] in showcase | mine],
                  key=lambda a: (a['id'] not in mine, display_name(a['name'])))


def option_label(analysis):
    source = 'your run' if analysis['id'] in mine else 'showcase'
    return f"{display_name(analysis['name'])} ({source})"


if len(analyses) < 2:
    st.info('You need at least two completed runs to compare. Run a scenario, or check the showcase.')
    footer(ui_config)
    st.stop()

cols = st.columns(2)
selected = []
for i, col in enumerate(cols):
    choice = col.selectbox(f'Run {i + 1}', options=analyses, format_func=option_label, index=None,
                           placeholder='Choose a run', key=f'compare_run_{i}')
    if choice:
        selected.append(choice)

if len(selected) != 2:
    st.info('Select 2 runs.')
    footer(ui_config)
    st.stop()

selected = pd.DataFrame(selected)
selected['name'] = selected['name'].map(display_name)

analysis_ids = [selected['id'][i] for i in range(2)]
model_ids = [selected['model'][i] for i in range(2)]

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
def get_analysis_inputs(ID, modified=None):  # `modified` busts the cache after a re-run
    return client_interface.analyses.get_file(ID, 'input_file', df=True)


@st.cache_data
def get_analysis_outputs(ID, modified=None):  # `modified` busts the cache after a re-run
    return client_interface.analyses.get_file(ID, 'output_file', df=True)


def get_location_df(inputs):
    """Return the locations DataFrame from an `input_file` dict, whichever
    of `location.csv` or `location.parquet` is present.
    """
    if not inputs:
        return None
    if 'location.csv' in inputs:
        return inputs['location.csv']
    if 'location.parquet' in inputs:
        return inputs['location.parquet']
    return None


analysis_settings = []
model_settings = []
with cols[0]:
    st.write(f"## {selected['name'][0]}")
    with st.spinner("Loading data..."):
        inputs = get_analysis_inputs(analysis_ids[0], selected['modified'][0])
        analysis_settings.append(client.analyses.settings.get(analysis_ids[0]).json())
        model_settings.append(client_interface.models.settings.get(model_ids[0]))

    with st.spinner('Loading analysis summary...'):
        summarise_inputs(get_location_df(inputs), analysis_settings[0], model_settings[0], title_prefix='###')

with cols[1]:
    st.write(f"## {selected['name'][1]}")
    with st.spinner("Loading data..."):
        inputs = get_analysis_inputs(analysis_ids[1], selected['modified'][1])
        analysis_settings.append(client.analyses.settings.get(analysis_ids[1]).json())
        model_settings.append(client_interface.models.settings.get(model_ids[1]))

    with st.spinner('Loading analysis summary...'):
        summarise_inputs(get_location_df(inputs), analysis_settings[1], model_settings[1], title_prefix='###')


@st.cache_data
def get_locations_file(ID):
    inputs = client_interface.analyses.get_file(ID, 'input_file', df=True)
    return get_location_df(inputs)


@st.cache_data
def merge_locations(locations_1, locations_2):
    """Concatenate locations for comparison and add `loc_analysis_id` identifier."""
    if locations_1 is None or locations_2 is None:
        return None

    filter_cols = {'LocNumber', 'Longitude', 'Latitude', 'CountryCode'}

    filter_cols = filter_cols.intersection(locations_1.columns)
    filter_cols = filter_cols.intersection(locations_2.columns)
    filter_cols = list(filter_cols)

    locations_1 = locations_1[filter_cols]
    locations_2 = locations_2[filter_cols]

    locations_1['loc_analysis_id'] = 1
    locations_2['loc_analysis_id'] = 2

    locations = pd.concat([locations_1, locations_2])

    return locations


perspectives = ['gul', 'il', 'ri']

st.write("# Loss estimates")
'This section enables comparison of the scenario loss from each of the analyses.'

for p in perspectives:
    if not all([s.get(f'{p}_output', False) for s in analysis_settings]):
        continue

    summaries = [s.get(f'{p}_summaries', [{}])[0] for s in analysis_settings]
    names = selected['name'].tolist()  # 'GUL OUTPUT' SHOULD BE MORE UNDERSTANDABLE FOR NON-EXPERT USERS BY USING TITLE 'GROUND UP LOSS'

    ord_settings = [s.get('ord_output', {}) or {} for s in summaries]

    ept_settings = [
        'ept_full_uncertainty_aep',
        'ept_full_uncertainty_oep',
        'ept_mean_sample_aep',
        'ept_mean_sample_oep',
        'ept_per_sample_mean_aep',
        'ept_per_sample_mean_oep'
    ]

    supported_outputs = ['aalcalc', 'eltcalc', 'lec_output']
    supported_ord_outputs = ['elt_moment', 'elt_quantile', 'plt_moment',
                             'plt_quantile', 'alt_meanonly', 'alt_period']

    has_legacy = any(all(s.get(output, False) for s in summaries) for output in supported_outputs)
    has_ord = any(all(o.get(output, False) for o in ord_settings) for output in supported_ord_outputs)
    has_ept = all(any(o.get(e, False) for e in ept_settings) for o in ord_settings)

    if has_legacy or has_ord or has_ept:
        st.write(f"## {PERSPECTIVES_MAP[p]} Output")
    else:
        st.error('No comparison available.')

    with st.spinner("Loading data..."):
        outputs = [OutputInterface(get_analysis_outputs(id, modified))
                   for id, modified in zip(analysis_ids, selected['modified'])]

    for output, s in zip(outputs, summaries):
        oed_fields = s.get('oed_fields', None)
        if oed_fields is not None:
            output.set_oed_fields(p, oed_fields)

    def produced(output_type, p=p, outputs=outputs):
        """Both runs produced this output (requested outputs can be missing)."""
        return all(o.has_output(p, output_type) for o in outputs)

    if all([s.get('aalcalc', False) for s in summaries]) and produced('aalcalc'):
        st.write("### Mean loss comparison chart")
        generate_aalcalc_comparison_fragment(p, outputs, names)

    if all([s.get('eltcalc', False) for s in summaries]) and produced('eltcalc'):
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
        generate_leccalc_comparison_fragment(p, outputs, names=names,
                                             lec_outputs=lec_outputs)

    if all(o.get('elt_moment', False) for o in ord_settings) and produced('elt_moment'):
        st.write("### MELT Output")
        locations = [get_locations_file(id) for id in analysis_ids]
        locations = merge_locations(*locations)
        generate_eltcalc_comparison_fragment(p, outputs, names=names,
                                             locations=locations,
                                             output_type='elt_moment',
                                             filter_col='SampleType',
                                             data_cols=['MeanLoss', 'MeanImpactedExposure', 'MaxImpactedExposure'],
                                             event_id='EventId',
                                             name_map={
                                                 'MeanLoss': 'Mean Loss',
                                                 'MeanImpactedExposure': 'Mean Impacted Exposure',
                                                 'MaxImpactedExposure': 'Max Impacted Exposure',
                                             })

    if all(o.get('elt_quantile', False) for o in ord_settings) and produced('elt_quantile'):
        st.write("### QELT Output")
        locations = [get_locations_file(id) for id in analysis_ids]
        locations = merge_locations(*locations)
        generate_eltcalc_comparison_fragment(p, outputs, names=names,
                                             locations=locations,
                                             output_type='elt_quantile',
                                             filter_col='Quantile',
                                             filter_label='Quantile Filter:',
                                             filter_index=-1,
                                             data_cols=['Loss'],
                                             event_id='EventId')

    if all(o.get('plt_moment', False) for o in ord_settings) and produced('plt_moment'):
        st.write("### MPLT Output")
        generate_pltcalc_comparison_fragment(p, outputs, names=names,
                                             output_type='plt_moment',
                                             filter_col='SampleType',
                                             value_col_options=['MeanLoss', 'MaxLoss',
                                                                'MeanImpactedExposure',
                                                                'MaxImpactedExposure'])

    if all(o.get('plt_quantile', False) for o in ord_settings) and produced('plt_quantile'):
        st.write("### QPLT Output")
        generate_pltcalc_comparison_fragment(p, outputs, names=names,
                                             output_type='plt_quantile',
                                             filter_col='Quantile',
                                             filter_label='Quantile Filter: ',
                                             filter_format_func=lambda x: '{:.2f}'.format(x),
                                             value_col='Loss')

    if all(o.get('alt_meanonly', False) for o in ord_settings) and produced('alt_meanonly'):
        st.write("### ALT MeanOnly Output")
        generate_alt_comparison_fragment(p, outputs, 'alt_meanonly', names=names)

    if all(o.get('alt_period', False) for o in ord_settings) and produced('alt_period'):
        st.write("### PALT Output")
        generate_alt_comparison_fragment(p, outputs, 'alt_period', names=names)

    if all(any(o.get(e, False) for e in ept_settings) for o in ord_settings) and produced('ept'):
        st.write("### EPT Output")
        ep_type_map = {1: 'OEP', 2: 'OEP TVAR', 3: 'AEP', 4: 'AEP TVAR'}
        ep_calc_map = EP_CALC_LABELS
        generate_leccalc_comparison_fragment(p, outputs, names=names,
                                             output_type='ept',
                                             filter_specs=[
                                                 {'col': 'EPType', 'label': 'EP Curve Type: ', 'format_map': ep_type_map},
                                                 {'col': 'EPCalc', 'label': 'Calculation Method:', 'format_map': ep_calc_map},
                                             ],
                                             return_period_col='ReturnPeriod', loss_col='Loss',
                                             group_col_default='SummaryId')

footer(ui_config)
