# Module to display output of MDK
import streamlit as st
import pandas as pd
import logging
from oasis_data_manager.errors import OasisException

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
        curr_summary = {}
        p_summaries = analysis_settings[f'{p}_summaries'][0]
        output_options = [
            'eltcalc',
            'aalcalc',
            'aalcalcmeanonly',
            'pltcalc',
            'summarycalc']
        curr_summary['outputs'] = [o for o in output_options if p_summaries.get(o, False)]

        if p_summaries.get('lec_output', False):
            lec_dict = p_summaries.get('leccalc', {'full_uncertainty_aep': True})
            lec_opts = [
                'full_uncertainty_aep',
                'full_uncertainty_oep',
                'wheatsheaf_aep',
                'wheatsheaf_oep',
                'wheatsheaf_mean_aep',
                'wheatsheaf_mean_oep',
                'sample_mean_aep',
                'sample_mean_oep'
            ]
            if curr_summary.get('outputs'):
                curr_summary['outputs'] += [f'leccalc-{o}' for o in lec_opts if lec_dict.get(o, False)]
            else:
                curr_summary['outputs'] = [f'leccalc-{o}' for o in lec_opts if lec_dict.get(o, False)]

        oed_fields = p_summaries.get('oed_fields', None)
        if oed_fields:
            curr_summary['oed_fields'] = oed_fields
        summary.append(curr_summary)

    return pd.DataFrame(summary, index=active_perspectives)

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
        output_settings_summary = summarise_output_settings(analysis_settings)
        output_settings_summary = DataframeView(output_settings_summary, hide_index=False)
        output_settings_summary.column_config['oed_fields'] = st.column_config.ListColumn('OED Fields')
        output_settings_summary.column_config['outputs'] = st.column_config.ListColumn('Outputs')
        output_settings_summary.display()


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


def eltcalc_table(perspective, vis_interface, oed_fields = []):
    if oed_fields:
        group_fields = st.pills("Group Columns",
                                oed_fields,
                                key=f'{perspective}_group_pill',
                                selection_mode='multi')
    else:
        group_fields = []

    group_fields = ['type'] + group_fields
    try:
        eltcalc_df = vis_interface.get(summary_level=1,
                                       perspective=perspective,
                                       output_type='eltcalc',
                                       group_fields=group_fields,
                                       categorical_cols=oed_fields)
    except OasisException:
        return None

    # Sort by loss
    eltcalc_df = eltcalc_df.sort_values('mean', ascending=False)

    df_memory = eltcalc_df.memory_usage().sum() / 1e6

    if df_memory > 200:
        st.error('Output too large, try grouping')
        logger.error(f'eltcalc view df size: {df_memory}')
    else:
        eltcalc_df = DataframeView(eltcalc_df)
        eltcalc_df.column_config['mean'] = st.column_config.NumberColumn('Mean', format='%.2f')
        for c in oed_fields:
            eltcalc_df.column_config[c] = st.column_config.ListColumn(c)
        # fix type column heading
        eltcalc_df.column_config['type'] = st.column_config.ListColumn('Type')

        eltcalc_df.display()

def eltcalc_map(perspective, vis_interface, locations, oed_fields = [], map_type = None):
    '''
    Generate MapView of output of eltcalc. Either `heatmap` or `choropleth` depending on portfolio.
    '''

    if map_type == 'choropleth':
        group_fields = ['CountryCode']
        eltcalc_df = vis_interface.get(summary_level=1,
                                       perspective=perspective,
                                       output_type='eltcalc',
                                       group_fields=group_fields,
                                       categorical_cols = oed_fields,
                                       filter_type = 2) # Only output sample

        mv = MapView(eltcalc_df, weight="mean", map_type="choropleth")
        mv.display()
        return

    if map_type == 'heatmap':
        group_fields = ['LocNumber']
        eltcalc_df = vis_interface.get(summary_level=1,
                                       perspective=perspective,
                                       output_type='eltcalc',
                                       group_fields=group_fields,
                                       categorical_cols = oed_fields,
                                       filter_type = 2) # Only output sample data
        loc_reduced = locations[['LocNumber', 'Longitude', 'Latitude']]
        heatmap_data = eltcalc_df.merge(loc_reduced, how="left", on="LocNumber")
        heatmap_data = heatmap_data[['Longitude', 'Latitude', 'mean']]

        mv = MapView(heatmap_data, longitude='Longitude', latitude='Latitude',
                     map_type='heatmap', weight='mean')
        mv.display()

def generate_eltcalc_fragment(perspective, vis_interface,
                              table = True, map = False, locations = None):
    '''
    Generate an `eltcalc` visualisation. Currently supports the `table`
    and `map` visualisation.
    For `map` visualisation, a `locations` dataframe is required.

    Parameters
    ----------
    perspective : str
                  Chosen perspective `gul`, `il` or `ri`.
    vis_interface : OutputVisualisationInterface
    table : bool
            If `True` displays table view.
    map : bool
          If `True` displays map view.
    locations : DataFrame
                DataFrame representing `locations.csv` file. Required for `map` view.

    '''
    oed_fields = vis_interface.oed_fields.get(perspective, [])

    tab_names = []
    if table:
        tab_names.append('table')
    if map:
        tab_names.append('map')

    if len(tab_names) == 0:
        return None

    tabs = st.tabs([t.title() for t in tab_names])

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

    for name, tab in zip(tab_names, tabs):
        if name == 'map':
            assert locations is not None, "Locations required for map view."
            map_type = None

            if 'LocNumber' in vis_interface.oed_fields.get(perspective, []) and valid_locations(locations):
                map_type = 'heatmap'
            elif 'CountryCode' in vis_interface.oed_fields.get(perspective, []):
                map_type = 'choropleth'

            with tab:
                eltcalc_map(perspective, vis_interface, locations, oed_fields, map_type)
        elif name == 'table':
            with tab:
                eltcalc_table(perspective, vis_interface, oed_fields)
