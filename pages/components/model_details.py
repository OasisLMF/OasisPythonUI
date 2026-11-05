'''
Schema-driven display of a model's settings (`model_settings.json`).
'''
import json

import pandas as pd
import streamlit as st

from modules import schemas
from modules.schemas import CATEGORICAL_MODEL_SETTINGS, PARAMETER_TYPES, PERSPECTIVE_LABELS


def _fmt(value):
    if isinstance(value, (list, tuple)):
        return ', '.join(f'`{v}`' for v in value) if value else '—'
    if isinstance(value, dict):
        return f'`{json.dumps(value)}`'
    if value is None or value == '':
        return '—'
    return f'`{value}`' if not isinstance(value, str) or ' ' not in value else value


def _field(label, value, help=None):
    left, right = st.columns([0.3, 0.7])
    left.markdown(f'**{label}**', help=help)
    right.markdown(_fmt(value))


def model_overview(model, settings):
    st.markdown(settings.get('description') or ':grey[No description provided.]')

    _field('Supplier', model.get('supplier_id'))
    _field('Model', model.get('model_id'))
    _field('Version', model.get('version_id'))
    _field('Run mode', model.get('run_mode'))
    _field('Settings version', settings.get('version'))

    default_samples = schemas.model_property('model_default_samples')
    _field(schemas.title(default_samples, 'Default samples'), settings.get('model_default_samples'),
           default_samples.get('description'))

    ms = settings.get('model_settings', {})
    perspectives = ms.get('valid_output_perspectives')
    entry = schemas.model_settings_property('valid_output_perspectives')
    _field(schemas.title(entry, 'Output perspectives'),
           [PERSPECTIVE_LABELS.get(p, p) for p in perspectives] if perspectives else 'All',
           entry.get('description'))

    data_settings = settings.get('data_settings', {})
    ds_schema = schemas.model_property('data_settings').get('properties', {})
    for key, value in data_settings.items():
        entry = ds_schema.get(key, {})
        _field(schemas.title(entry, key), value, entry.get('description'))


def model_perils(settings):
    perils = settings.get('lookup_settings', {}).get('supported_perils')
    if not perils:
        st.caption('The model does not list its supported perils.')
        return
    df = pd.DataFrame(perils).rename(columns={'id': 'Peril code', 'desc': 'Description',
                                              'peril_correlation_group': 'Correlation group'})
    st.dataframe(df, hide_index=True)


def model_options(settings):
    '''Categorical selectors (event set, footprint set, ...) and their options.'''
    ms = settings.get('model_settings', {})
    found = False
    for key in CATEGORICAL_MODEL_SETTINGS:
        if key not in ms:
            continue
        found = True
        option = ms[key]
        entry = schemas.model_settings_property(key)
        with st.container(border=True):
            st.markdown(f"**{option.get('name') or schemas.title(entry, key)}**",
                        help=option.get('tooltip') or entry.get('description'))
            if option.get('desc'):
                st.caption(option['desc'])
            options = pd.DataFrame(option.get('options', []))
            if not options.empty:
                options.insert(0, 'Default', options['id'] == option.get('default'))
                options = options.rename(columns={'id': 'ID', 'desc': 'Description'})
                st.dataframe(options, hide_index=True)
    if not found:
        st.caption('The model has no selectable event, footprint or vulnerability sets.')


def model_parameters(settings):
    '''User-settable model parameters, grouped as the model defines.'''
    ms = settings.get('model_settings', {})
    rows = []
    for key, kind in PARAMETER_TYPES.items():
        for p in ms.get(key, []):
            if p.get('visible') is False:
                continue
            row = {
                'Parameter': p.get('name'),
                'Description': p.get('desc'),
                'Type': kind,
                'Default': json.dumps(p.get('default')) if isinstance(p.get('default'), (list, dict)) else p.get('default'),
                'Range': f"{p['min']} – {p['max']}" if 'min' in p and 'max' in p else None,
                'Options': ', '.join(str(o.get('id', o)) for o in p.get('options', [])) or None,
                'Used for': p.get('used_for'),
                'Editable': p.get('editable', True),
            }
            rows.append(row)

    if not rows:
        st.caption('The model has no additional parameters.')
        return

    df = pd.DataFrame(rows).astype({'Default': 'string'})
    df = df.dropna(axis='columns', how='all')

    groups = sorted(ms.get('parameter_groups', []), key=lambda g: g.get('priority_id', 0))
    grouped = set()
    for group in groups:
        members = [n for n in group.get('presentation_order', []) if n in set(df['Parameter'])]
        if not members:
            continue
        grouped.update(members)
        st.markdown(f"**{group.get('desc') or group.get('name')}**", help=group.get('tooltip'))
        st.dataframe(df.set_index('Parameter').loc[members].reset_index(), hide_index=True)

    rest = df[~df['Parameter'].isin(grouped)]
    if not rest.empty:
        if grouped:
            st.markdown('**Other parameters**')
        st.dataframe(rest, hide_index=True)


def model_details(model, settings):
    if not settings:
        st.warning('No model settings have been registered for this model.')
        return

    overview, options, parameters, perils, raw = st.tabs(
        ['Overview', 'Run options', 'Parameters', 'Perils', 'Settings JSON'])
    with overview:
        model_overview(model, settings)
    with options:
        model_options(settings)
    with parameters:
        model_parameters(settings)
    with perils:
        model_perils(settings)
    with raw:
        st.json(settings, expanded=2)
        st.download_button('Download model_settings.json', json.dumps(settings, indent=2),
                           file_name=f"{model.get('model_id', 'model')}_model_settings.json",
                           key=f"download_model_settings_{model['id']}")
