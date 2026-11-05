'''
Standalone script for AppTest coverage of `analysis_settings_editor`.

Uses a model whose settings exercise every parameter type, parameter groups
and restricted output perspectives. Results are stored in session state as
`editor_settings`, `editor_valid` and `editor_problems`. Set
`session_state['base_settings']` before running to start from a template.
'''
import streamlit as st

from pages.components.settings_editor import analysis_settings_editor

MODEL = {'id': 1, 'supplier_id': 'Supplier', 'model_id': 'TestModel', 'version_id': '1'}

MODEL_SETTINGS = {
    'name': 'Test model',
    'model_default_samples': 7,
    'model_settings': {
        'event_set': {
            'name': 'Event Set', 'desc': 'Event set selection', 'default': 'p',
            'options': [{'id': 'p', 'desc': 'Probabilistic'}, {'id': 'h', 'desc': 'Historic'}],
        },
        'valid_output_perspectives': ['gul', 'il'],
        'boolean_parameters': [{'name': 'use_surge', 'desc': 'Include storm surge', 'default': True}],
        'float_parameters': [{'name': 'demand_surge', 'desc': 'Demand surge factor', 'default': 1.1,
                              'min': 1.0, 'max': 2.0, 'stepsize': 0.05}],
        'integer_parameters': [{'name': 'max_events', 'desc': 'Maximum events', 'default': 100}],
        'numeric_parameters': [{'name': 'scale', 'desc': 'Hazard scale', 'default': 0.5}],
        'string_parameters': [{'name': 'tag', 'desc': 'Run tag', 'default': 'base'}],
        'list_parameters': [{'name': 'regions', 'desc': 'Regions', 'default': ['north', 'south']}],
        'dictionary_parameters': [{'name': 'weights', 'desc': 'Weights', 'default': {'a': 1}}],
        'dropdown_parameters': [{'name': 'vuln_curve', 'desc': 'Vulnerability curve', 'default': 'mid',
                                 'options': [{'id': 'low', 'desc': 'Low'}, {'id': 'mid', 'desc': 'Mid'}]}],
        'parameter_groups': [{'name': 'hazard', 'desc': 'Hazard options', 'priority_id': 1,
                              'presentation_order': ['use_surge', 'demand_surge', 'scale']}],
    },
    'lookup_settings': {'supported_perils': [{'id': 'WTC', 'desc': 'Tropical cyclone'},
                                             {'id': 'WSS', 'desc': 'Storm surge'}]},
    'data_settings': {'damage_group_fields': ['PortNumber', 'AccNumber', 'LocNumber']},
}

# Accounts file but no reinsurance files: IL possible, RI not
PORTFOLIO = {'id': 1, 'name': 'p', 'location_file': {'stored': 'l.csv'}, 'accounts_file': {'stored': 'a.csv'}}

settings, valid, problems = analysis_settings_editor(
    MODEL, MODEL_SETTINGS, PORTFOLIO, st.session_state.get('base_settings'), key='test_editor')
st.session_state['editor_settings'] = settings
st.session_state['editor_valid'] = valid
st.session_state['editor_problems'] = problems
