# Module to display output of MDK
import streamlit as st
import pandas as pd
import logging
import plotly.express as px
import plotly.graph_objects as go
from math import log10

from pages.components.display import DataframeView, MapView

logger = logging.getLogger(__name__)


def summarise_locations(locations):
    summary = pd.Series()

    # summary info
    summary['number_locations'] = locations.shape[0]

    # add tiv sums
    tiv_cols = ['BuildingTIV', 'OtherTIV', 'ContentsTIV', 'BITIV']
    tiv_cols = [c for c in tiv_cols if c in locations.columns]
    sums = locations[tiv_cols].sum()
    summary = pd.concat((summary, sums))

    summary['TotalTIV'] = sums.sum()

    return pd.DataFrame(summary).T


def summarise_model_settings(model_settings):
    return pd.DataFrame([pd.Series(model_settings)])

def summarise_analysis_settings(analysis_settings):
    summary = pd.Series()

    # add model details
    keys = ['model_name_id', 'model_supplier_id', 'number_of_samples']
    for k in keys:
        val = analysis_settings.get(k, None)
        if val:
            summary[k] = val

    # perspectives summary
    perspectives = ['gul', 'il', 'ri']
    active_perspectives = [p for p in perspectives if analysis_settings.get(f'{p}_output', False)]
    summary['perspectives'] = active_perspectives

    return pd.DataFrame([summary])

def summarise_output_settings(analysis_settings):
    perspectives = ['gul', 'il', 'ri']
    active_perspectives = [p for p in perspectives if analysis_settings.get(f'{p}_output', False)]

    summary = []
    for p in active_perspectives:
        curr_summary = {'outputs': []}
        p_summaries = analysis_settings[f'{p}_summaries'][0]
        output_options = [
            'eltcalc',
            'aalcalc',
            'aalcalcmeanonly',
            'pltcalc',
            'summarycalc']
        curr_summary['outputs'] += [o for o in output_options if p_summaries.get(o, False)]

        if p_summaries.get('lec_output', False):
            lec_dict = p_summaries.get('leccalc', {'full_uncertainty_aep': True})
            lec_opts = {
                'full_uncertainty_aep': 'full_uncertainty_aep',
                'full_uncertainty_oep': 'full_uncertainty_oep',
                'wheatsheaf_aep': 'persample_aep',
                'wheatsheaf_oep': 'persample_oep',
                'wheatsheaf_mean_aep': 'persample_mean_aep',
                'wheatsheaf_mean_oep': 'persample_mean_oep',
                'sample_mean_aep': 'sample_mean_aep',
                'sample_mean_oep': 'sample_mean_oep'
            }
            curr_summary['outputs'] += [f'leccalc-{v}' for k, v in lec_opts.items() if lec_dict.get(k, False)]

        # ord ouput settings
        ord_output = p_summaries.get('ord_output', None)

        if ord_output:
            curr_summary['ord_outputs'] = []

            valid_options = [
                'elt_sample', 'elt_quantile', 'elt_moment', 'plt_sample',
                'plt_quantile', 'plt_moment', 'alt_period', 'alt_meanonly',
                'alct_convergence',
                'ept_full_uncertainty_aep', 'ept_full_uncertainty_oep',
                'ept_mean_sample_aep', 'ept_mean_sample_oep',
                'ept_per_sample_mean_aep', 'ept_per_sample_mean_oep',
                'psept_aep', 'psept_oep'
            ]

            for opt in valid_options:
                if ord_output.get(opt, False):
                    curr_summary['ord_outputs'].append(opt)

        oed_fields = p_summaries.get('oed_fields', None)
        if oed_fields:
            curr_summary['oed_fields'] = oed_fields
        summary.append(curr_summary)

    return pd.DataFrame(summary, index=active_perspectives)

def summarise_summary_levels(summary_settings):
    '''
    Take a list of summary sets from the analysis settings and produce a list of summaries of each level.

    Returns
        List[dict] where each dict corresponds to a single summary level with
        the following keys for each summary level:
            - `id` - summary level id
            - `ord_output` - list of ord outputs
            - `legacy_outputs` - list of legacy outputs
            - `oed_fields` - list of oed group fields
    '''
    return [summarise_summary_level(level) for level in summary_settings]

def summarise_summary_level(summary_level_settings):
    '''Summarise a single summary set from the analysis settings.
    '''
    curr_summary = {}

    # Handle ord outputs
    ord_output = summary_level_settings.get('ord_output', None)
    ord_outputs_list = []

    if ord_output:
        valid_options = [
            'elt_sample', 'elt_quantile', 'elt_moment', 'plt_sample',
            'plt_quantile', 'plt_moment', 'alt_period', 'alt_meanonly',
            'alct_convergence',
            'ept_full_uncertainty_aep', 'ept_full_uncertainty_oep',
            'ept_mean_sample_aep', 'ept_mean_sample_oep',
            'ept_per_sample_mean_aep', 'ept_per_sample_mean_oep',
            'psept_aep', 'psept_oep'
        ]

        for opt in valid_options:
            if ord_output.get(opt, False):
                    ord_outputs_list.append(opt)
    curr_summary['ord_output'] = ord_outputs_list

    ## Handle legacy outputs

    output_options = [
        'eltcalc',
        'aalcalc',
        'aalcalcmeanonly',
        'pltcalc',
        'summarycalc']

    legacy_outputs = [o for o in output_options if summary_level_settings.get(o, False)]

    if summary_level_settings.get('lec_output', False):
        lec_dict = summary_level_settings.get('leccalc', {})
        lec_opts = {
            'full_uncertainty_aep': 'full_uncertainty_aep',
            'full_uncertainty_oep': 'full_uncertainty_oep',
            'wheatsheaf_aep': 'persample_aep',
            'wheatsheaf_oep': 'persample_oep',
            'wheatsheaf_mean_aep': 'persample_mean_aep',
            'wheatsheaf_mean_oep': 'persample_mean_oep',
            'sample_mean_aep': 'sample_mean_aep',
            'sample_mean_oep': 'sample_mean_oep'
        }

        legacy_outputs += [f'leccalc-{v}' for k, v in lec_opts.items() if lec_dict.get(k, False)]

    curr_summary['legacy_output'] = legacy_outputs

    curr_summary['oed_fields'] = summary_level_settings.get('oed_fields', [])
    curr_summary['level_id'] = summary_level_settings['id']
    return curr_summary

def summarise_inputs(locations=None, analysis_settings=None, title_prefix='##'):
    if locations is None and analysis_settings is None:
        st.info('No locations or analysis settings.')

    if locations is not None:
        st.markdown(f'{title_prefix} Input Summary')
        loc_summary = summarise_locations(locations)
        loc_summary = DataframeView(loc_summary)
        loc_summary.display()

    if analysis_settings is not None:
        st.markdown(f'{title_prefix} Analysis Settings')
        a_settings_summary = summarise_analysis_settings(analysis_settings)
        a_settings_summary = DataframeView(a_settings_summary)
        a_settings_summary.column_config['perspectives'] = st.column_config.ListColumn('Perspectives')
        a_settings_summary.display()

    if analysis_settings and 'model_settings' in analysis_settings.keys():
        st.markdown(f'{title_prefix} Model Settings')
        m_settings_summary = summarise_model_settings(analysis_settings['model_settings'])
        m_settings_summary = DataframeView(m_settings_summary)
        m_settings_summary.display()

    if analysis_settings is not None:
        st.markdown(f'{title_prefix} Output Settings')
        perspectives = ["gul", "il", "ri"]
        tabs = st.tabs([p.upper() for p in perspectives])
        for p, t in zip(perspectives, tabs):
            with t:
                summaries = analysis_settings.get(f"{p}_summaries", None)
                if summaries is not None:
                    ViewSummarySettings(summaries, key=f"show_{p}_summaries_view")
                else:
                    st.info("No summary settings found.")


def ViewSummarySettings(summary_settings, key=None, selectable=False):
    '''
    Display the summary settings for a single perspective as a selectable dataframe.

    Args:
        summary_settings (list[dict]): List of summary settings to display.

    Returns:
        (int) `id` for selected summary settings.

    '''
    summaries = summarise_summary_levels(summary_settings)
    summaries = pd.DataFrame(summaries)
    cols = ['level_id', 'ord_output', 'legacy_output', 'oed_fields']
    summaries = DataframeView(summaries, display_cols=cols, selectable=selectable)
    summaries.column_config['ord_output'] = st.column_config.ListColumn('ORD Output')
    summaries.column_config['legacy_output'] = st.column_config.ListColumn('Legacy Output')
    summaries.column_config['oed_fields'] = st.column_config.ListColumn('OED Fields')

    selected = summaries.display(key=key)
    return selected['level_id'].iloc[0] if selected is not None else None


def show_settings(settings_list):
    """
    Displays abstract settings list. Settings are dict like objects with a
    `parameter` specifying the setting parameter name and `value` which is a
    display of the value of the setting parameter.
    """
    for d in settings_list:
        cols = st.columns([0.2, 0.8])
        logger.info(f"Generating Model Details: {settings_list}")
        with cols[0]:
            st.write(f'**{d["parameter"]}:**')
        with cols[1]:
            if getattr(d["value"], 'display', None):
                d["value"].display()
            else:
                st.write(f'{d["value"]}')


def model_summary(model, model_settings, detail_level="full"):
    """
    Create a summary view of the model settings for the selected model.

    Currently supports the following fields:

    ```
    model_id : Name
    supplier_id : Supplier
    model_settings
        description : Description
        model_settings
            event_set
                options: Event Set Options
                default: Ecent Set Default
            event_occurence_id
                options: Event Occurrence ID Options
                default: Event Occurrence ID Default
        lookup_settings
            supported_perils : Supported Perils
        data_settings
           hazard_group_fields : Hazard Group Fields
           damage_group_fields : Damage Group Fields

    ```

    Parameters
    ----------
    model : dict
            Model query response.
    model_settings: dict
                    Model settings query response.
    detail_level: str
                  "full" produces the full model detail.
                  "minimal" only displays the model `Name`, `Supplier` and `Description`.
    """
    settings_list = [
            {'parameter': 'Name', 'value': model.get('model_id', '')},
            {'parameter': 'Supplier', 'value': model.get('supplier_id', '')},
            {'parameter': 'Description', 'value': model_settings.get('description', '')},
           ]

    if detail_level == "minimal":
        show_settings(settings_list)
        return

    if "model_settings" in model_settings:
        _model_settings = model_settings["model_settings"]

        if "event_set" in _model_settings:
            es_options = _model_settings["event_set"].get('options', [])
            if len(es_options) > 0:
                es_options = pd.DataFrame(es_options)
                es_options_view = DataframeView(es_options)
                es_options_view.column_config['desc'] = 'Description'
                settings_list.append({'parameter': 'Event Set Options', 'value': es_options_view})
            if _model_settings["event_set"].get("default", None):
                settings_list.append({'parameter': 'Event Set Default',
                            'value': f'`{_model_settings["event_set"]["default"]}`'})

        if "event_occurrence_id" in _model_settings:
            eo_options = _model_settings["event_occurrence_id"].get('options', [])
            if len(eo_options) > 0:
                eo_options = pd.DataFrame(eo_options)
                eo_options_view = DataframeView(eo_options)
                eo_options_view.column_config['desc'] = 'Description'
                settings_list.append({'parameter': 'Event Occurrence ID Options', 'value': eo_options_view})
            if _model_settings["event_occurrence_id"].get("default", None):
                settings_list.append({'parameter': 'Event Occurrence ID Default',
                            'value': f'`{_model_settings["event_occurrence_id"]["default"]}`'})

    if "lookup_settings" in model_settings:
        lookup_settings = model_settings.get("lookup_settings")

        if "supported_perils" in lookup_settings:
            perils = pd.DataFrame(lookup_settings["supported_perils"])
            display_cols = ['id', 'desc']
            peril_view = DataframeView(perils, display_cols=display_cols)
            column_config = {
                'id': st.column_config.TextColumn('Peril Code'),
                'desc': st.column_config.TextColumn('Description')
            }
            peril_view.column_config = column_config
            settings_list.append({'parameter': 'Supported Perils', 'value': peril_view})

    if "data_settings" in model_settings:
        data_settings = model_settings["data_settings"]

        if "hazard_group_fields" in data_settings:
            group_field_str = '`'
            group_field_str += '`, `'.join(data_settings["hazard_group_fields"])
            group_field_str += '`'
            settings_list.append({"parameter": "Hazard Group Fields", "value": group_field_str})

        if "damage_group_fields" in data_settings:
            group_field_str = '`'
            group_field_str += '`, `'.join(data_settings["damage_group_fields"])
            group_field_str += '`'
            settings_list.append({"parameter": "Damage Group Fields", "value": group_field_str})

    show_settings(settings_list)

def elt_group_fields(df, group_fields, agg_dict=None, categorical_cols=[]):
    if agg_dict is None:
        agg_dict = {}

    if categorical_cols is None:
        categorical_cols = []

    ungrouped_cols = df.columns.difference(group_fields)
    numeric_cols = df.select_dtypes(include='number').columns
    numeric_cols = numeric_cols.difference(categorical_cols)
    numeric_cols = numeric_cols.intersection(ungrouped_cols)
    non_numeric_cols = ungrouped_cols.difference(numeric_cols)

    for c in numeric_cols:
        if agg_dict.get(c, None) is None:
            agg_dict[c] = 'sum'
    for c in non_numeric_cols:
        if agg_dict.get(c, None) is None:
            agg_dict[c] = 'unique'

    @st.cache_data(show_spinner=False, max_entries=1000)
    def eltcalc_transform(df, group_fields, agg_dict):
        return df.groupby(group_fields, as_index=False).agg(agg_dict)

    return eltcalc_transform(df, group_fields, agg_dict)


def oed_fields_group(oed_fields, key_prefix=None, selection_mode='multi'):
    if key_prefix is None:
        key_prefix = ''

    group_fields = st.pills("Group Columns",
                            oed_fields,
                            key=f'{key_prefix}_elt_group_pill',
                            selection_mode=selection_mode)

    return group_fields

def elt_ord_table(result, perspective, oed_fields = None, key_prefix=None,
                  order_cols=None, data_cols=None, name_map = {},
                  event_id='EventId', additional_cols=None, selectable=False):
    table_df = result
    if key_prefix is None:
        key_prefix = ''

    if oed_fields is None:
        oed_fields = []

    if data_cols is None:
        data_cols = []

    if additional_cols is None:
        additional_cols = []

    # Ordering
    if order_cols:
        if len(order_cols) > 1:
            order_col = st.radio('Sort By: ', options=order_cols, index=0, horizontal=True,
                                 format_func = lambda x: name_map.get(x, x),
                                 key=f'{key_prefix}_elt_ord_order_col')
        else:
            order_col = order_cols[0]

        table_df = table_df.sort_values(by=order_col, ascending=False)

    # OED Filters
    with st.popover("OED Filters", use_container_width=True):
        for oed_field in oed_fields:
            options = table_df[oed_field].unique()
            oed_filter = st.multiselect(f"{oed_field} Filter:",  options,
                                         key=f'{key_prefix}_{oed_field}_elt_filter')

            if oed_filter:
                table_df = table_df[table_df[oed_field].isin(oed_filter)]

    cols = [event_id] + additional_cols + oed_fields + data_cols
    table_view = DataframeView(table_df, display_cols=cols, selectable=selectable)

    for c in data_cols:
        table_view.column_config[c] = st.column_config.NumberColumn(name_map.get(c, c),
                                                                      format='%.2f')
    for c in oed_fields:
        table_view.column_config[c] = st.column_config.ListColumn(name_map.get(c, c))
    for c in additional_cols:
        table_view.column_config[c] = st.column_config.ListColumn(name_map.get(c, c))
    table_view.column_config[event_id] = st.column_config.ListColumn('Event ID')

    selected = table_view.display()

    if selectable:
        return table_df, selected
    return table_df

def eltcalc_table(eltcalc_result, perspective, oed_fields=None, show_cols=None,
                  key_prefix=None):
    if key_prefix is None:
        key_prefix = ''

    if oed_fields is None:
        oed_fields = []

    if show_cols is None:
        show_cols = ['mean'] if 'mean' in eltcalc_result.columns else []

    if 'SampleType' in eltcalc_result.columns:
        type_col = ['SampleType']
    elif 'type' in eltcalc_result.columns:
        type_col = ['type']
    else:
        type_col = []

    group_fields = oed_fields_group(oed_fields,
                                    key_prefix=f'{key_prefix}_{perspective}')
    group_fields = type_col + group_fields
    table_df = elt_group_fields(eltcalc_result, group_fields, categorical_cols=oed_fields)


    cols = type_col + oed_fields + show_cols
    table_df = table_df[cols]

    # Sort by loss
    table_df = table_df.sort_values(show_cols, ascending=False)

    df_memory = table_df.memory_usage().sum() / 1e6

    if df_memory > 200:
        st.error('Output too large, try grouping')
        logger.error(f'eltcalc view df size: {df_memory}')
    else:
        table_view = DataframeView(table_df, display_cols = cols)
        for col in show_cols:
            table_view.column_config[col] = st.column_config.NumberColumn(col, format='%.2f')
        for c in oed_fields:
            table_view.column_config[c] = st.column_config.ListColumn(c)
        if type_col:
            formatted_type = 'Type' if type_col[0] == 'type' else type_col[0]
            table_view.column_config[type_col[0]] = st.column_config.ListColumn(formatted_type)

        table_view.display()

def eltcalc_map(map_df, locations, oed_fields=[], map_type=None,
                intensity_col='mean'):
    '''
    Generate MapView of output of eltcalc. Either `heatmap` or `choropleth` depending on portfolio.
    '''
    map_df = map_df[[intensity_col] + oed_fields]

    if map_type == 'choropleth':
        group_fields = ['CountryCode']
        map_df = elt_group_fields(map_df, group_fields, categorical_cols=oed_fields)

        mv = MapView(map_df, weight=intensity_col, map_type="choropleth")
        mv.display()
        return

    if map_type == 'heatmap':
        group_fields = ['LocNumber']
        map_df = elt_group_fields(map_df, group_fields, categorical_cols=oed_fields)

        loc_reduced = locations[['LocNumber', 'Longitude', 'Latitude']]
        map_df = map_df.merge(loc_reduced, how="left", on="LocNumber")
        map_df = map_df[['Longitude', 'Latitude', intensity_col]]

        mv = MapView(map_df, longitude='Longitude', latitude='Latitude',
                     map_type='heatmap', weight=intensity_col)
        mv.display()
        return

    st.info("No map to display.")

def valid_locations(loc_df):
    '''
    Check if `Latitude` and `Longitude` columns are present
    and if they are unique between locations.
    '''
    if loc_df is None:
        return False
    if not set(['Latitude', 'Longitude']).issubset(loc_df.columns):
        return False

    lat_long = loc_df[['Latitude', 'Longitude']]
    if (lat_long == lat_long.iloc[0]).all(axis=None):
        return False

    return True


@st.fragment
def generate_eltcalc_fragment(perspective, output,
                              table = True, map = False, locations = None):
    '''
    Generate an `eltcalc` visualisation. Currently supports the `table`
    and `map` visualisation.
    For `map` visualisation, a `locations` dataframe is required.

    Parameters
    ----------
    perspective : str
                  Chosen perspective `gul`, `il` or `ri`.
    vis_interface : OutputInterface
    table : bool
            If `True` displays table view.
    map : bool
          If `True` displays map view.
    locations : DataFrame
                DataFrame representing `locations.csv` file. Required for `map` view.

    '''
    oed_fields = output.oed_fields.get(perspective, [])
    eltcalc_result = output.get(1, perspective, 'eltcalc')

    tab_names = []
    if table:
        tab_names.append('table')
    if map:
        tab_names.append('map')

    if len(tab_names) == 0:
        return None

    tabs = st.tabs([t.title() for t in tab_names])

    for name, tab in zip(tab_names, tabs):
        if name == 'map':
            assert locations is not None, "Locations required for map view."
            map_type = None

            if 'LocNumber' in oed_fields and valid_locations(locations):
                map_type = 'heatmap'
            elif 'CountryCode' in oed_fields:
                map_type = 'choropleth'

            with tab:
                map_df = eltcalc_result[eltcalc_result['type'] == 'Sample']
                eltcalc_map(map_df, locations, oed_fields, map_type)
        elif name == 'table':
            with tab:
                eltcalc_table(eltcalc_result, perspective, oed_fields)

@st.fragment
def generate_melt_fragment(p, vis, locations=None):
    data_df = vis.get(1, p, 'elt_moment')
    oed_fields = vis.oed_fields.get(p)

    # Type filter
    if 'type' in data_df.columns:
        type_col = 'type'
    elif 'SampleType' in data_df.columns:
        type_col = 'SampleType'
    else:
        type_col = None

    if type_col:
        types = data_df[type_col].unique()
        selected_type = st.radio('Type Filter:', options=types, index=0, horizontal=True,
                                 key=f'melt_elt_ord_type_filter')
        data_df = data_df[data_df[type_col] == selected_type]

    map_event_container = st.container()

    tab_names = ['table', 'map']
    with st.container(border=True):
        tabs = st.tabs([t.title() for t in tab_names])

    with tabs[0]:
        data_df, selected = elt_ord_table(data_df, perspective=p, oed_fields=oed_fields,
                                 order_cols=['MeanLoss','MeanImpactedExposure',
                                             'MaxImpactedExposure'],
                                 data_cols=['MeanLoss','MeanImpactedExposure',
                                            'MaxImpactedExposure'],
                                 key_prefix='melt',
                                 selectable='multi')

    selected_events = []
    if selected is not None and not selected.empty:
        selected_events = selected['EventId'].tolist()

    if locations is None:
        with tabs[1]:
            st.error("Map view unavailable.")
        logger.error("Locations required for Map view")
        return

    map_type = None

    if 'LocNumber' in oed_fields and valid_locations(locations):
        map_type = 'heatmap'
    elif 'CountryCode' in oed_fields:
        map_type = 'choropleth'

    if selected_events:
        data_df = data_df[data_df['EventId'].isin(selected_events)]

    with tabs[1]:
        if len(selected_events) > 0:
            data = pd.DataFrame(
                {'EventId':[selected_events] }
            )
            st.dataframe(data,
                         column_config= {'EventId' : st.column_config.ListColumn('Mapped EventIds')},
                         hide_index=True)
        loss_col = st.radio('Intensity Column:', ['MeanLoss', 'MeanImpactedExposure', 'MaxImpactedExposure'],
                            index=0, horizontal=True)
        eltcalc_map(data_df, locations, oed_fields, map_type,
                    intensity_col=loss_col)


@st.fragment
def generate_qelt_fragment(p, vis, locations=None):
    data_df = vis.get(1, p, 'elt_quantile')
    oed_fields = vis.oed_fields.get(p)

    options = data_df['Quantile'].unique()
    quantile_filter = st.radio("Quantile Filter", options,
                               horizontal=True, index=len(options) - 1)

    data_df = data_df[data_df['Quantile'] == quantile_filter]

    map_event_container = st.container()

    tab_names = ['table', 'map']
    with st.container(border=True):
        tabs = st.tabs([t.title() for t in tab_names])

    with tabs[0]:
        table_df, selected = elt_ord_table(data_df, perspective=p,
                                 oed_fields=oed_fields, key_prefix='qelt',
                                 order_cols=['Loss'], data_cols=['Loss'],
                                 selectable="multi")

    selected_events = []
    if selected is not None and not selected.empty:
        selected_events = selected['EventId'].tolist()


    if locations is None:
        with tabs[1]:
            st.error("Map view unavailable.")
        logger.error("Locations required for Map view")
        return

    map_type = None

    if 'LocNumber' in oed_fields and valid_locations(locations):
        map_type = 'heatmap'
    elif 'CountryCode' in oed_fields:
        map_type = 'choropleth'

    map_df = data_df
    if selected_events:
        map_df = data_df[data_df['EventId'].isin(selected_events)]

    with tabs[1]:
        if len(selected_events) > 0:
            data = pd.DataFrame(
                {'EventId':[selected_events] }
            )
            st.dataframe(data,
                         column_config= {'EventId' : st.column_config.ListColumn('Mapped EventIds')},
                         hide_index=True)
        eltcalc_map(map_df, locations, oed_fields, map_type,
                    intensity_col='Loss')
    return


@st.fragment
def generate_aalcalc_fragment(p, vis):
    result = vis.get(1, p, 'aalcalc')

    oed_fields = vis.oed_fields.get(p)
    breakdown_field = None
    if oed_fields and len(oed_fields) > 0:
        breakdown_field = st.pills('Breakdown OED Field: ', options=oed_fields)

    breakdown_field_invalid = False
    if breakdown_field and result[breakdown_field].nunique() > 100:
        breakdown_field_invalid = True
        breakdown_field = None

    group_field = ['type']

    if breakdown_field:
        result[breakdown_field] = result[breakdown_field].astype(str)
        group_field += [breakdown_field]

    result = result.loc[:, group_field + ['mean']]
    result = result.groupby(group_field, as_index=False).agg({'mean': 'sum'})

    graph = px.bar(result, x='type', y='mean', color=breakdown_field,
                   labels = {'type': 'Type', 'mean': 'Mean'},
                   color_discrete_sequence= px.colors.sequential.RdBu)

    if breakdown_field_invalid:
        st.error("Too many values in group field.")

    st.plotly_chart(graph, use_container_width=True)

@st.fragment
def generate_alt_fragment(p, vis, output_type='alt_meanonly'):
    result = vis.get(1, p, output_type)
    type_field = 'SampleType'
    mean_field = 'MeanLoss'

    oed_fields = vis.oed_fields.get(p)
    breakdown_field = None
    if oed_fields and len(oed_fields) > 0:
        breakdown_field = st.pills('Breakdown OED Field: ', options=oed_fields,
                                   key=f'{output_type}_oed_filter')

    breakdown_field_invalid = False
    if breakdown_field and result[breakdown_field].nunique() > 100:
        breakdown_field_invalid = True
        breakdown_field = None

    group_field = [type_field]

    if breakdown_field:
        result[breakdown_field] = result[breakdown_field].astype(str)
        group_field += [breakdown_field]

    result = result.loc[:, group_field + [mean_field]]
    result = result.groupby(group_field, as_index=False).agg({mean_field: 'sum'})

    type_formatted = type_field[0] + type_field[1:]
    mean_formatted = mean_field[0] + mean_field[1:]
    graph = px.bar(result, x=type_field, y=mean_field, color=breakdown_field,
                   labels = {type_field: type_formatted, mean_field: mean_formatted},
                   color_discrete_sequence= px.colors.sequential.RdBu)

    if breakdown_field_invalid:
        st.error("Too many values in group field.")

    st.plotly_chart(graph, use_container_width=True, key=f'{output_type}_graph')

def generate_leccalc_fragment(p, vis, lec_outputs):
    lec_options = [option for option in lec_outputs.keys() if lec_outputs[option]]
    option = st.pills('Select Output:', options=lec_options)

    if option is None:
        st.info('Output option not selected.')
    else:
        analysis_type = '_'.join(option.split('_')[:-1])
        loss_type = option.split('_')[-1]
        result = vis.get(1, p, 'leccalc', analysis_type = analysis_type, loss_type = loss_type)
        oed_fields = vis.oed_fields.get(p)

        selected_group = None
        if oed_fields and len(oed_fields) > 0:
            selected_group = st.pills('Grouped OED Field: ', options=oed_fields, key='leccalc_group_field_pills')

        if selected_group is None:
            selected_group = 'summary_id'

        if analysis_type == "wheatsheaf":
            result_plot = result.groupby(["summary_id", "return_period"] + oed_fields, as_index=False).agg(min_loss = ("loss", "min"),
                                                                                              max_loss = ("loss", "max"),
                                                                                              mean_loss = ("loss", "mean"))

            result_plot = result_plot[[selected_group, "return_period", "mean_loss", "max_loss", "min_loss"]]
            result_plot = result_plot.groupby([selected_group, 'return_period'], as_index=False).agg({'mean_loss': 'sum',
                                                                                                       'max_loss': 'sum',
                                                                                                       'min_loss': 'sum',
                                                                                                      })
            result_plot = result_plot.sort_values(by=["return_period", "mean_loss"], ascending=[True, False])

        else:
            result_plot = result[[selected_group, 'return_period', 'type', 'loss']]
            result_plot = result_plot.groupby([selected_group, 'return_period', 'type'],
                                              as_index=False).agg({'loss': 'sum'})
            result_plot = result_plot.sort_values(by=['return_period', 'loss'], ascending=[True, False])

        log_x = log10(result_plot['return_period'].max()) - log10(result_plot['return_period'].min()) > 2
        unique_group = result_plot[selected_group].unique().tolist()

        if len(unique_group) > 5:
            filter_group = st.multiselect(f'Filtered {selected_group} Values:',
                                          options = unique_group,
                                          default = unique_group[:5])
            result_plot = result_plot[result_plot[selected_group].isin(filter_group)]


        if analysis_type == "wheatsheaf":
            fig = go.Figure()
            for item in result_plot[selected_group].unique().tolist():
                result_item = result_plot[result_plot[selected_group] == item]
                fig.add_trace(go.Scatter(
                    x = result_item["return_period"],
                    y = result_item["mean_loss"],
                    error_y = {'array': result_item["max_loss"],
                               'arrayminus': result_item["min_loss"]},
                    name = item))
                fig.update_layout(
                    xaxis = dict(title = dict(text = 'Return Period')),
                    yaxis = dict(title = dict(text = 'Loss')),
                    legend_title_text=selected_group,
                    showlegend=True
                )
                if log_x:
                    fig.update_xaxes(type="log")

        else:
            fig = px.line(result_plot, x='return_period', y='loss',
                          color=selected_group, line_dash='type', markers=False,
                          labels = {'return_period': 'Return Period', 'loss':
                                    'Loss', 'type': 'Type',
                                    selected_group: selected_group},
                          line_group='type',
                          log_x=log_x)
        st.plotly_chart(fig)

def generate_leccalc_comparison_fragment(perspective, outputs, lec_outputs, names=[]):
    '''
    Compare outputs from leccalc. Note that 'per_sample' or 'wheatsheaf' plots are not supported.

    Parameters
    ----------
    perspective : str
                  Perspective of output. 'gul', 'il' or 'ri'
    outputs : List[OutputInterface]
              Lists of `OutputInterface` containing the outputs to compare.
    lec_outputs : List[str]
                  List of leccalc output types.
    names : List[str]
            Names of each analysis references to by `outputs`.
    '''
    lec_options = [option for option in lec_outputs.keys() if lec_outputs[option]]
    lec_options = [opt for opt in lec_options if opt not in ['wheatsheaf_aep', 'wheatsheaf_oep']]

    def format_lec_options(opt):
        analysis_type = '_'.join(opt.split('_')[:-1])
        loss_type = opt.split('_')[-1]

        analysis_type = analysis_type.replace('wheatsheaf', 'per_sample')
        return f'{analysis_type}_{loss_type}'

    option = st.pills('Select Output:', options=lec_options,
                      format_func=format_lec_options)

    diff_names = len(outputs) - len(names)
    offset = len(names)
    if diff_names > 0:
        for i in range(diff_names):
            names.append(f'Analysis {i + offset + 1}')

    if len(outputs) > 2:
        st.error('Maximum 2 outputs for comparison')
        logger.error(f'Too many outputs for leccalc comparison plot.\nOutputs: {outputs}')
        return

    if option is None:
        st.info('Output option not selected.')
        return

    analysis_type = '_'.join(option.split('_')[:-1])
    loss_type = option.split('_')[-1]

    results = [o.get(1, perspective, 'leccalc', analysis_type = analysis_type, loss_type = loss_type) for o in outputs]

    types = set()
    for r in results:
        types.update(r['type'].unique().tolist())
    selected_type = st.radio('Type Filter:', options=types, index=0, horizontal=True,
                             key=f'{perspective}_lec_comparison_type_filter')
    for i in range(len(results)):
        results[i] = results[i][results[i]['type'] == selected_type]

    oed_fields = shared_oed_fields(perspective, outputs)

    selected_group = None
    if oed_fields and len(oed_fields) > 0:
        selected_group = st.pills('Grouped OED Field: ', options=oed_fields, key='leccalc_group_field_pills')

    if selected_group is None:
        selected_group = 'summary_id'

    name_map = {i: names[i] for i in range(2)}
    selected_analysis = st.segmented_control('Analysis Filter:',
                                             options=name_map.keys(),
                                             format_func = lambda x: name_map.get(x, x),
                                             key=f'{perspective}_lec_name_filter')

    linestyles = ['dash', None]
    if selected_analysis is not None:
        results = [results[selected_analysis]]
        names = [names[selected_analysis]]
        linestyles = [linestyles[selected_analysis]]

    results_plot = []
    for result in results:
        result_plot = result[[selected_group, 'return_period', 'loss']]
        result_plot = result_plot.groupby([selected_group, 'return_period'],
                                          as_index=False).agg({'loss': 'sum'})
        result_plot = result_plot.sort_values(by=['return_period', 'loss'], ascending=[True, False])
        results_plot.append(result_plot)

    log_x = [log10(result_plot['return_period'].max()) - log10(result_plot['return_period'].min()) > 2 for result_plot in results_plot]
    log_x = any(log_x)

    unique_group = []
    for result_plot in results_plot:
        unique_group += result_plot[selected_group].unique().tolist()
    unique_group = list(set(unique_group))

    graphed_group_fields = unique_group
    if len(unique_group) > 5:
        filter_group = st.multiselect(f'Filtered {selected_group} Values:',
                                      options = unique_group,
                                      default = unique_group[:5])
        for i in range(len(results_plot)):
            results_plot[i] = results_plot[i][results_plot[i][selected_group].isin(filter_group)]
        graphed_group_fields = filter_group


    fig = go.Figure()
    colors = px.colors.qualitative.Plotly
    j = 0
    for result, name in zip(results_plot, names):
        for i, field in enumerate(graphed_group_fields):
            curr_result = result[result[selected_group] == field]
            hover_title = f'{name} - {field}'
            fig.add_trace(go.Scatter(x=curr_result['return_period'], y=curr_result['loss'], name=field, legendgroup=name,
                                     legendgrouptitle_text=name,
                                     line=dict(color=colors[i % len(colors)], dash=linestyles[j % 2]),
                                     hovertemplate= hover_title + '<br>Return Period: %{x}'+
                                                   '<br><b>Loss: %{y}</b>',
                                     customdata=[f'{name}']))
        j += 1

    fig.update_layout(
        xaxis=dict(title=dict(text='Loss'), type="log" if log_x else None),
        yaxis=dict(title=dict(text='Return Period')),
        hovermode='closest',
        showlegend=True
    )

    st.plotly_chart(fig)

@st.cache_data(show_spinner='Creating pltcalc bar')
def pltcalc_bar(result, selected_group=None, number_shown=10, date_id = False,
                year='Year', month='Month', day='Day', loss='MeanLoss'):
    '''
    Bar plot of pltcalc output ranked by loss in descending order by year.

    Parameters
    ----------
    result : pd.DataFrame
             pltcalc results dataframe.
    selected_group : str
                     Column to group by.
    number_shown : int
                   Number of years to show.
    date_id : bool
              If `True` then pltcalc produced data with a `date_id` column.
              Otherwise `occ_year`, `occ_month` and `occ_day` columns expected
              in `result`.
    '''
    if not date_id:
        result[[year, month, day]] = result[[year, month, day]].astype(str)
        result[year] = result[year].str.zfill(result[year].str.len().max())
        result[month] = result[month].str.zfill(2)
        result[day] = result[day].str.zfill(2)
        result['date_id'] = result[[year, month, day]].agg('-'.join, axis=1)

    if selected_group:
        result_df = result[[selected_group, 'date_id', loss]]
    else:
        result_df = result[['date_id', loss]]

    ranked_dates = result_df.groupby('date_id', as_index=False).agg({loss: 'sum'}).sort_values(by=loss, ascending=False)

    ranked_dates = ranked_dates.iloc[:number_shown]
    ranked_dates = ranked_dates.rename(columns={loss: f'total_{loss}'})

    result_df = result_df[result_df['date_id'].isin(ranked_dates['date_id'])]
    result_df = pd.merge(result_df, ranked_dates, how='left', on='date_id')

    if selected_group:
        result_df = result_df.groupby([selected_group, 'date_id'], as_index=False).agg({loss: 'sum', f'total_{loss}': 'first'})
    else:
        result_df = result_df.groupby(['date_id'], as_index=False).agg({loss: 'sum', f'total_{loss}': 'first'})

    if len(loss) > 1:
        loss_formatted = loss[0].upper() + loss[1:]
    else:
        loss_formatted = loss

    fig = px.bar(result_df, x='date_id', y=loss, color=selected_group,
                 hover_data={
                     f'total_{loss}': ':s'
                 },
                 labels={'date_id': 'Date', f'total_{loss}': f'Total {loss_formatted}', loss: loss_formatted})
    fig.update_xaxes(type='category', categoryorder='array',
                     categoryarray=ranked_dates['date_id'])

    return fig

@st.fragment
def generate_pltcalc_fragment(p, vis):
    result = vis.get(1, p, 'pltcalc')
    oed_fields = vis.oed_fields.get(p)

    selected_group = None
    if oed_fields and len(oed_fields) > 0 :
        selected_group = st.pills('Grouped OED Field: ', options=oed_fields, key='pltcalc_group_field_pills')

    selected_group_invalid = False
    if selected_group and result[selected_group].nunique() > 100:
        selected_group_invalid = True
        selected_group = None
    elif selected_group:
        result[selected_group] = result[selected_group].astype(str)

    types = result['type'].unique()
    selected_type = st.radio('Type filter: ', options=types, index=0)

    result = result[result['type'] == selected_type]

    date_cols = {
        'year': 'occ_year',
        'month': 'occ_month',
        'day': 'occ_day'
    }

    with st.spinner('Generating pltcalc...'):
        if set(date_cols.values()).issubset(result.columns):
            fig = pltcalc_bar(result, selected_group, date_id=False, loss='mean',  **date_cols)
        else:
            fig = pltcalc_bar(result, selected_group, date_id=True, loss='mean')
    st.plotly_chart(fig)
    if selected_group_invalid:
        st.error("Too many values in group field.")

@st.fragment
def generate_mplt_fragment(p, vis):
    result = vis.get(1, p, 'plt_moment')
    oed_fields = vis.oed_fields.get(p)

    selected_group = None
    if oed_fields and len(oed_fields) > 0 :
        selected_group = st.pills('Grouped OED Field: ', options=oed_fields, key=f'mplt_{p}_group_field_pills')

    selected_group_invalid = False
    if selected_group and result[selected_group].nunique() > 100:
        selected_group_invalid = True
        selected_group = None
    elif selected_group:
        result[selected_group] = result[selected_group].astype(str)

    types = result['SampleType'].unique()
    selected_type = st.radio('Type filter: ', options=types, index=0, horizontal=True)

    result = result[result['SampleType'] == selected_type]

    date_cols = {
        'year': 'Year',
        'month': 'Month',
        'day': 'Day'
    }

    loss_col = st.radio('Loss Filter: ', options=['MeanLoss', 'MaxLoss',
                                                  'MeanImpactedExposure',
                                                  'MaxImpactedExposure'], horizontal=True)

    with st.spinner('Generating pltcalc...'):
        fig = pltcalc_bar(result, selected_group, date_id=False, loss=loss_col, **date_cols)

    if selected_group_invalid:
        st.error("Too many values in group field.")
    st.plotly_chart(fig)

@st.fragment
def generate_qplt_fragment(p, vis):
    result = vis.get(1, p, 'plt_quantile')
    oed_fields = vis.oed_fields.get(p)

    selected_group = None
    if oed_fields and len(oed_fields) > 0 :
        selected_group = st.pills('Grouped OED Field: ', options=oed_fields, key=f'qplt_{p}_group_field_pills')

    selected_group_invalid = False
    if selected_group and result[selected_group].nunique() > 100:
        selected_group_invalid = True
        selected_group = None
    elif selected_group:
        result[selected_group] = result[selected_group].astype(str)

    quantiles = result['Quantile'].unique()
    quantile_filter = st.radio('Quantile Filter: ', options=quantiles,
                               horizontal=True,
                               format_func=lambda x: '{:.2f}'.format(x))
    date_cols = {
        'year': 'Year',
        'month': 'Month',
        'day': 'Day'
    }

    result = result[result['Quantile'] == quantile_filter]
    with st.spinner('Generating pltcalc...'):
        fig = pltcalc_bar(result, selected_group, date_id=False, loss="Loss", **date_cols)

    if selected_group_invalid:
        st.error("Too many values in group field.")
    st.plotly_chart(fig)

@st.fragment
def generate_ept_fragment(p, vis):
    result = vis.get(1, p, 'ept')

    ep_type_map = {
        1 : 'OEP',
        2 : 'OEP TVAR',
        3 : 'AEP',
        4 : 'AEP TVAR'
    }

    ep_calc_map = {
        1 : 'MeanDR',
        2 :  'Full',
        3 :  'PerSampleMean',
        4 :  'MeanSample'
    }

    type_options = result['EPType'].unique()
    calc_options = result['EPCalc'].unique()

    if len(type_options) > 1:
        selected_type = st.radio('EP Curve Type: ', options=type_options, horizontal=True,
                                 format_func= lambda x: ep_type_map.get(x, x))

        result = result[result['EPType'] == selected_type]

    selected_calc = None
    if len(calc_options) > 1:
        selected_calc = st.radio("Calculation Method:", options=calc_options, horizontal=True,
                                 format_func=lambda x: ep_calc_map.get(x, x))
        result = result[result['EPCalc'] == selected_calc]

    oed_fields = vis.oed_fields.get(p)

    selected_group = None
    if oed_fields and len(oed_fields) > 0 :
        selected_group = st.pills('Grouped OED Field: ', options=oed_fields, key=f'qplt_{p}_group_field_pills')

    if selected_group is None:
        selected_group = 'SummaryId'

    result = result[[selected_group, 'ReturnPeriod', 'Loss']]
    result = result.groupby([selected_group, 'ReturnPeriod'],
                            as_index=False).agg({'Loss': 'sum'})

    max_return_period = result['ReturnPeriod'].max()
    unique_group = result[result['ReturnPeriod'] == max_return_period].sort_values(by='Loss', ascending=False)
    unique_group = unique_group[selected_group].tolist()

    result = result.sort_values(by=['ReturnPeriod', 'Loss'], ascending=[True, False])
    log_x = log10(result['ReturnPeriod'].max()) - log10(result['ReturnPeriod'].min()) > 2

    all_selected = result[selected_group].unique().tolist()
    unique_group += [e for e in all_selected if e not in unique_group]

    if len(unique_group) > 5:
        filter_group = st.multiselect(f'Filtered {selected_group} Values:',
                                      options = unique_group,
                                      default = unique_group[:5])
        result = result[result[selected_group].isin(filter_group)]

    fig = px.line(result, x='ReturnPeriod', y='Loss',
                  color=selected_group, markers=False,
                  labels = {'ReturnPeriod': 'Return Period'},
                  log_x=log_x)
    st.plotly_chart(fig)

def shared_oed_fields(p, outputs):
    oed_fields = outputs[0].oed_fields.get(p)
    return list(set(oed_fields) & set(outputs[1].oed_fields.get(p)))

def generate_aalcalc_comparison_fragment(p, outputs, names = None):
    results = [o.get(1, p, 'aalcalc') for o in outputs]

    oed_fields = shared_oed_fields(p, outputs)
    breakdown_field = None
    if oed_fields and len(oed_fields) > 0:
        breakdown_field = st.pills('Breakdown OED Field: ', options=oed_fields)

    breakdown_field_invalid = False
    if breakdown_field and any([r[breakdown_field].nunique() > 100 for r in results]):
        breakdown_field_invalid = True
        breakdown_field = None

    types = results[0]['type'].unique()
    selected_type = st.radio('Type filter: ', options=types, index=0, horizontal=True)

    for i in range(2):
        results[i] = results[i][results[i]['type'] == selected_type]

    group_field = []
    if breakdown_field:
        for i in range(2):
            results[i][breakdown_field] = results[i][breakdown_field].astype(str)
        group_field += [breakdown_field]

    results = list(map(lambda x: x.loc[:, group_field + ['mean']], results))

    if len(group_field) > 0:
        results = list(map(lambda x: x.groupby(group_field, as_index=False).agg({'mean': 'sum'}), results))

    if names is None:
        names = ['Analysis 1', 'Analysis 2']

    for i in range(2):
        results[i]['name'] = names[i]

    results = pd.concat(results)
    if breakdown_field is None:
        results = results.groupby('name', as_index=False).agg({'mean': 'sum'})

    graph = px.bar(results, x='name', y='mean', color=breakdown_field,
                   labels = {'mean': 'Mean', 'name': 'Analysis Name'},
                   color_discrete_sequence= px.colors.sequential.RdBu,
                   category_orders={'name': names})
    st.plotly_chart(graph, use_container_width=True)

    if breakdown_field_invalid:
        st.error("Too many values in group field.")

def generate_eltcalc_comparison_fragment(perspective, outputs, names=None,
                                         locations=None):
    results = [o.get(1, perspective, 'eltcalc') for o in outputs]
    oed_fields = shared_oed_fields(perspective, outputs)

    types = results[0]['type'].unique()

    selected_type = st.radio('Type Filter:', options=types, index=0, horizontal=True,
                             key=f'{perspective}_elt_comparison_type_filter')

    for i in range(len(results)):
        results[i] = results[i][results[i]['type'] == selected_type]
        results[i]['name'] = names[i] if names[i] else f'Analysis {i+1}'


    name_map = {i: names[i] for i in range(2)}
    selected_analysis = st.segmented_control('Analysis Filter:',
                                             options=name_map.keys(),
                                             format_func = lambda x: name_map.get(x, x),
                                             key=f'{perspective}_elt_name_filter')

    if selected_analysis is not None:
        result = results[selected_analysis]
    else:
        result = pd.concat(results)

    table_tab, map_tab = st.tabs(['Table', 'Map'])

    with table_tab:
        result, selected = elt_ord_table(result, perspective=perspective, oed_fields=oed_fields,
                                 order_cols=['mean','exposure_value'],
                                 data_cols = ['mean', 'exposure_value'],
                                 key_prefix=f'{perspective}_elt', event_id='event_id',
                                 additional_cols=['name'],
                                 name_map = {
                                        'mean': 'Mean',
                                        'exposure_value': 'Exposure Value',
                                        'name': 'Analysis Name'
                                    },
                                 selectable='multi')

    cols = st.columns(2)
    mapped_events = {}
    for i in range(2):
        with cols[i]:
            analysis_name = results[i]['name'].loc[0]
            default_session_variable = f'elt_default_events_analysis_{i}'

            if default_session_variable not in st.session_state:
                st.session_state[default_session_variable] = []
                curr_default = []
            else:
                curr_default = st.session_state[default_session_variable]

            if selected is not None:
                curr_default += selected[selected['name'] == analysis_name]['event_id'].unique().tolist()
                curr_default = list(set(curr_default))
            curr_event_ids = result[result['name'] == analysis_name]['event_id'].unique()
            curr_default = [d for d in curr_default if d in curr_event_ids]
            curr_events = st.multiselect(f'{analysis_name} Mapped Events:', options=curr_event_ids,
                                         default=curr_default,
                                         key=f'elt_{perspective}_selectbox_events_{i}')

            if len(curr_event_ids) > 0:
                st.session_state[default_session_variable] = curr_events
            mapped_events[analysis_name] = curr_events

    with map_tab:
        if locations is None:
            st.info('Locations files not found.')
            return

        map_type = None

        if 'LocNumber' in oed_fields and valid_locations(locations):
            map_type = 'heatmap'
        elif 'CountryCode' in oed_fields:
            map_type = 'choropleth'

        if all([len(v) > 0 for v in mapped_events.values()]):
            results = []

            for k, v in mapped_events.items():
                curr_result = result[result['name'] == k]
                curr_result = curr_result[curr_result['event_id'].isin(v)]
                results.append(curr_result)
            result = pd.concat(results)

        eltcalc_map(result, locations, oed_fields, map_type=map_type,
                    intensity_col='mean')
