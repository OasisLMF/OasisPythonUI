# Module to display output of MDK
import streamlit as st
import pandas as pd

from pages.components.display import DataframeView

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
    keys = ['model_name_id', 'model_supplier_id']
    for k in keys:
        val = analysis_settings.get(k, None)
        if val:
            summary[k] = val

    # perspectives summary
    perspectives = ['gul', 'il', 'ri']
    active_perspectives = [p for p in perspectives if analysis_settings.get(f'{p}_output', False)]
    summary['perspectives'] = active_perspectives

    # grouping view
    oed_groupings = []
    for p in active_perspectives:
        oed_fields =  analysis_settings[f'{p}_summaries'][0].get('oed_fields', None)
        if oed_fields:
            oed_groupings.extend(oed_fields)
    oed_groupings = set(oed_groupings)

    if len(oed_groupings) > 0:
        summary['oed_fields'] = oed_groupings

    return pd.DataFrame([summary])


def summarise_intputs(locations=None, analysis_settings=None, title_prefix='##'):
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
        if 'oed_fields' in a_settings_summary.column_config:
            a_settings_summary.column_config['oed_fields'] = st.column_config.ListColumn('OED Fields')
        a_settings_summary.display()

    if analysis_settings and 'model_settings' in analysis_settings.keys():
        st.markdown(f'{title_prefix} Model Settings')
        m_settings_summary = summarise_model_settings(analysis_settings['model_settings'])
        m_settings_summary = DataframeView(m_settings_summary)
        m_settings_summary.display()

