'''
Tests for the schema-driven analysis settings editor.
'''
import pytest
from streamlit.testing.v1 import AppTest

from modules import schemas
from pages.components.settings_editor import perspective_availability

APP = 'tests/fixtures/settings_editor_app.py'


@pytest.fixture
def editor():
    return AppTest.from_file(APP, default_timeout=30).run()


def test_defaults_are_valid(editor):
    at = editor
    assert not at.exception
    assert at.session_state['editor_valid'], at.session_state['editor_problems']

    settings = at.session_state['editor_settings']
    assert settings['model_supplier_id'] == 'Supplier'
    assert settings['model_name_id'] == 'TestModel'
    assert settings['number_of_samples'] == 7  # model_default_samples
    assert settings['gul_output'] is True
    assert settings['gul_summaries'][0]['ord_output']['elt_moment'] is True


def test_model_parameters_use_their_defaults(editor):
    ms = editor.session_state['editor_settings']['model_settings']
    assert ms == {
        'event_set': 'p',
        'use_surge': True,
        'demand_surge': 1.1,
        'max_events': 100,
        'scale': 0.5,
        'tag': 'base',
        'regions': ['north', 'south'],
        'weights': {'a': 1},
        'vuln_curve': 'mid',
    }


def test_controls_match_parameter_types(editor):
    at = editor
    assert at.selectbox(key='test_editor_ms_event_set').options == ['p – Probabilistic', 'h – Historic']
    assert at.toggle(key='test_editor_param_use_surge').value is True
    slider = at.slider(key='test_editor_param_demand_surge')
    assert (slider.min, slider.max, slider.step) == (1.0, 2.0, 0.05)
    assert at.number_input(key='test_editor_param_max_events').value == 100
    assert at.text_input(key='test_editor_param_tag').value == 'base'
    assert at.selectbox(key='test_editor_param_vuln_curve').value == 'mid'


def test_changing_controls_updates_settings(editor):
    at = editor
    at.selectbox(key='test_editor_ms_event_set').set_value('h')
    at.toggle(key='test_editor_param_use_surge').set_value(False)
    at.number_input(key='test_editor_samples').set_value(50)
    at.text_area(key='test_editor_param_regions').input('["east"]')
    at.run()

    settings = at.session_state['editor_settings']
    assert settings['number_of_samples'] == 50
    assert settings['model_settings']['event_set'] == 'h'
    assert settings['model_settings']['use_surge'] is False
    assert settings['model_settings']['regions'] == ['east']
    assert at.session_state['editor_valid']


def test_invalid_json_parameter_is_reported(editor):
    at = editor
    at.text_area(key='test_editor_param_weights').input('{not json').run()
    assert not at.session_state['editor_valid']
    assert any('Weights' in p for p in at.session_state['editor_problems'])


def test_return_periods_are_parsed(editor):
    at = editor
    at.text_input(key='test_editor_return_periods').input('10, 100, 1000').run()
    assert at.session_state['editor_settings']['return_periods'] == [10, 100, 1000]

    at.text_input(key='test_editor_return_periods').input('ten').run()
    assert not at.session_state['editor_valid']


def test_perspectives_respect_model_and_portfolio(editor):
    at = editor
    il = at.checkbox(key='test_editor_il_output')
    ri = at.checkbox(key='test_editor_ri_output')
    assert not il.disabled
    assert ri.disabled  # not in the model's valid perspectives

    il.check().run()
    settings = at.session_state['editor_settings']
    assert settings['il_output'] is True
    assert settings['il_summaries'] == settings['gul_summaries']
    assert settings['ri_output'] is False


def test_no_perspectives_is_invalid(editor):
    at = editor
    at.checkbox(key='test_editor_gul_output').uncheck().run()
    assert not at.session_state['editor_valid']
    assert 'Select at least one loss perspective.' in at.session_state['editor_problems']


def test_summary_level_group_by_and_outputs(editor):
    at = editor
    at.multiselect(key='test_editor_all_1_fields').set_value(['LocNumber'])
    at.checkbox(key='test_editor_all_1_plt_sample').check()
    at.checkbox(key='test_editor_all_1_elt_moment').uncheck()
    at.run()

    level = at.session_state['editor_settings']['gul_summaries'][0]
    assert level['oed_fields'] == ['LocNumber']
    assert level['ord_output']['plt_sample'] is True
    assert 'elt_moment' not in level['ord_output']


def test_add_and_remove_summary_levels(editor):
    at = editor
    at.button(key='test_editor_all_add').click().run()
    assert [lv['id'] for lv in at.session_state['editor_settings']['gul_summaries']] == [1, 2]

    at.button(key='test_editor_all_1_remove').click().run()
    assert [lv['id'] for lv in at.session_state['editor_settings']['gul_summaries']] == [2]


def test_template_values_are_loaded_and_unmanaged_keys_kept():
    at = AppTest.from_file(APP, default_timeout=30)
    at.session_state['base_settings'] = {
        'model_supplier_id': 'Other', 'model_name_id': 'Other',
        'number_of_samples': 3,
        'gul_threshold': 5.0,
        'source_tag': 'keep-me',
        'model_settings': {'event_set': 'h', 'tag': 'from-template'},
        'gul_output': True,
        'gul_summaries': [{'id': 4, 'oed_fields': ['AccNumber'], 'eltcalc': True,
                           'ord_output': {'elt_sample': True}}],
    }
    at.run()

    assert at.session_state['editor_valid'], at.session_state['editor_problems']
    settings = at.session_state['editor_settings']
    assert settings['model_name_id'] == 'TestModel'  # always the selected model
    assert settings['number_of_samples'] == 3
    assert settings['gul_threshold'] == 5.0
    assert settings['source_tag'] == 'keep-me'
    assert settings['model_settings']['event_set'] == 'h'
    assert settings['model_settings']['tag'] == 'from-template'

    level = settings['gul_summaries'][0]
    assert level['id'] == 4
    assert level['oed_fields'] == ['AccNumber']
    assert level['eltcalc'] is True  # legacy output preserved
    assert level['ord_output']['elt_sample'] is True


def test_perspective_availability():
    model_settings = {'model_settings': {}}
    loc_only = {'location_file': {'stored': 'l.csv'}}
    full = {f: {'stored': 'x.csv'} for f in
            ['location_file', 'accounts_file', 'reinsurance_info_file', 'reinsurance_scope_file']}

    assert set(perspective_availability(model_settings, loc_only)) == {'il', 'ri'}
    assert perspective_availability(model_settings, full) == {}
    gul_only = {'model_settings': {'valid_output_perspectives': ['gul']}}
    assert set(perspective_availability(gul_only, full)) == {'il', 'ri'}


def test_ord_output_groups_cover_schema():
    grouped = {k for keys in schemas.ORD_OUTPUT_GROUPS.values() for k in keys}
    assert grouped == set(schemas.ord_output_options())
