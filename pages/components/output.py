# Module to display output of MDK
import streamlit as st
import pandas as pd
import logging
from oasis_data_manager.errors import OasisException
from ods_tools.oed import AnalysisSettingSchema
import plotly.express as px
from plotly.colors import sample_colorscale
import plotly.graph_objects as go
from math import log10
from datetime import date, datetime

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
        output_settings_summary.column_config['ord_outputs'] = st.column_config.ListColumn('ORD Outputs')
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
        map_df = map_df[[intensity_col] + oed_fields]

        loc_reduced = locations[['LocNumber', 'Longitude', 'Latitude']]
        map_df = map_df.merge(loc_reduced, how="left", on="LocNumber")
        map_df = map_df[['Longitude', 'Latitude', intensity_col]]

        mv = MapView(map_df, longitude='Longitude', latitude='Latitude',
                     map_type='heatmap', weight=intensity_col)
        mv.display()
        return

    st.info("No map to display")

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
    vis_interface : OutputInterface
    table : bool
            If `True` displays table view.
    map : bool
          If `True` displays map view.
    locations : DataFrame
                DataFrame representing `locations.csv` file. Required for `map` view.

    '''
    oed_fields = vis_interface.oed_fields.get(perspective, [])
    eltcalc_result = vis_interface.get(1, perspective, 'eltcalc')

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
    result = vis.get(1, p, 'elt_moment')

    oed_fields = vis.oed_fields.get(p)

    tab_names = ['table', 'map']

    tabs = st.tabs([t.title() for t in tab_names])

    for name, tab in zip(tab_names, tabs):
        if name == 'map':
            if locations is None:
                with tab:
                    st.error("Map view unavailable.")
                logger.error("Locations required for Map view")
                continue

            map_type = None

            if 'LocNumber' in oed_fields and valid_locations(locations):
                map_type = 'heatmap'
            elif 'CountryCode' in oed_fields:
                map_type = 'choropleth'

            with tab:
                map_df = result[result['SampleType'] == 'Sample']
                loss_col = st.radio('Intensity Column:', ['MeanLoss', 'MeanImpactedExposure', 'MaxImpactedExposure'],
                                    index=0, horizontal=True)
                eltcalc_map(map_df, locations, oed_fields, map_type,
                            intensity_col=loss_col)
        elif name == 'table':
            with tab:
                eltcalc_table(result, perspective=p, oed_fields=oed_fields,
                              show_cols=['MeanLoss', 'MeanImpactedExposure', 'MaxImpactedExposure'],
                              key_prefix='melt')

@st.fragment
def generate_qelt_fragment(p, vis):
    result = vis.get(1, p, 'elt_quantile')
    oed_fields = vis.oed_fields.get(p)
    group_field = oed_fields_group(oed_fields,
                                    key_prefix=f'qelt_{p}',
                                    selection_mode='single')

    group_fields = ['Quantile']
    if group_field:
        group_fields.append(group_field)

    cols = ['Quantile'] + oed_fields + ['Loss']
    result = result[cols]
    df = elt_group_fields(result, group_fields, categorical_cols=oed_fields)

    quantiles = df['Quantile'].unique().tolist()
    quantiles = [str(q) for q in sorted(quantiles, reverse=True)]

    df['Quantile'] = df['Quantile'].astype(str)

    # Prep colours
    sample_points = [i/(len(quantiles) - 1) for i in range(0, len(quantiles))]
    colors = sample_colorscale('RdBu', sample_points)
    colors = {q:c for q, c in zip(quantiles, colors)}

    if group_field:
        unique_grouped = df[group_field].unique()
        if len(unique_grouped) > 1:
            value = min(20, len(unique_grouped))
            max_value = min(50, len(unique_grouped))
            n_show = st.slider("Number of Fields: ", step=1, value=value, max_value=max_value, min_value=1)
            df = df.sort_values("Loss", ascending=False)
            if len(unique_grouped) > n_show:
                st.info(f"Showing top {n_show} fields.")
                df = df[df[group_field].isin(unique_grouped[:n_show])]
        fig = px.bar(df, x=group_field, y='Loss', color='Quantile', barmode='overlay',
                     color_discrete_sequence=px.colors.sequential.RdBu,
                     color_discrete_map=colors,
                     category_orders={'Quantile': quantiles},
                     opacity=1)
        fig.update_xaxes(type='category')
    else:
        quantiles = reversed(quantiles)
        fig = px.bar(df, x = 'Quantile', y='Loss', color='Quantile',
                     color_discrete_map=colors,
                     category_orders={'Quantile': quantiles})
        fig.update_xaxes(type='category')
        fig.update_layout(showlegend=False)
    st.plotly_chart(fig)


@st.fragment
def generate_aalcalc_fragment(p, vis):
    result = vis.get(1, 'gul', 'aalcalc')

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

@st.cache_data(show_spinner='Creating pltcalc bar')
def pltcalc_bar(result, selected_group=None, number_shown=10, date_id = False):
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
        date_cols = ["occ_year", "occ_month", "occ_day"]
        result[date_cols] = result[date_cols].astype(str)
        result["occ_year"] = result["occ_year"].str.zfill(result["occ_year"].str.len().max())
        result["occ_month"] = result["occ_month"].str.zfill(2)
        result["occ_day"] = result["occ_day"].str.zfill(2)
        result['date_id'] = result[date_cols].agg('-'.join, axis=1)

    if selected_group:
        result_df = result[[selected_group, 'date_id', 'mean']]
    else:
        result_df = result[['date_id', 'mean']]

    ranked_dates = result_df.groupby('date_id', as_index=False).agg({'mean': 'sum'}).sort_values(by='mean', ascending=False)

    ranked_dates = ranked_dates.iloc[:number_shown]
    ranked_dates = ranked_dates.rename(columns={'mean': 'total_mean'})

    result_df = result_df[result_df['date_id'].isin(ranked_dates['date_id'])]
    result_df = pd.merge(result_df, ranked_dates, how='left', on='date_id')

    if selected_group:
        result_df = result_df.groupby([selected_group, 'date_id'], as_index=False).agg({'mean': 'sum', 'total_mean': 'first'})
    else:
        result_df = result_df.groupby(['date_id'], as_index=False).agg({'mean': 'sum', 'total_mean': 'first'})

    fig = px.bar(result_df, x='date_id', y='mean', color=selected_group,
                 hover_data={
                     'total_mean': ':s'
                 },
                 labels={'date_id': 'Date', 'total_mean': 'Total Mean', 'mean': 'Mean'})
    fig.update_xaxes(type='category', categoryorder='array',
                     categoryarray=ranked_dates['date_id'])

    return fig

@st.fragment
def generate_pltcalc_fragment(p, vis):
    result = vis.get(1, 'gul', 'pltcalc')
    oed_fields = vis.oed_fields.get(p)

    selected_group = None
    if oed_fields and len(oed_fields) > 0 :
        selected_group = st.pills('Grouped OED Field: ', options=oed_fields, key='leccalc_group_field_pills')

    selected_group_invalid = False
    if selected_group and result[selected_group].nunique() > 100:
        selected_group_invalid = True
        selected_group = None
    elif selected_group:
        result[selected_group] = result[selected_group].astype(str)

    types = result['type'].unique()
    selected_type = st.radio('Type filter: ', options=types, index=0)

    result = result[result['type'] == selected_type]

    with st.spinner('Generating pltcalc...'):
        if set(['occ_year', 'occ_month', 'occ_day']).issubset(result.columns):
            fig = pltcalc_bar(result, selected_group, date_id=False)
        else:
            fig = pltcalc_bar(result, selected_group, date_id=True)
    st.plotly_chart(fig)
    if selected_group_invalid:
        st.error(f"Too many values in group field.")
