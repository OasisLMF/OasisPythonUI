"""Tests for the public Scenarios app (scenarios_app.py)."""
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

import tests.mocks as m
from modules import scenarios as sc
from modules.client import ClientInterface

VID = 'aaaaaaaaaaaa'
OTHER = 'bbbbbbbbbbbb'

SETTINGS = {
    'model_supplier_id': 'OasisLMF', 'model_name_id': 'PiWind', 'number_of_samples': 10,
    'gul_output': True,
    'gul_summaries': [{'id': 1, 'ord_output': {'elt_sample': True, 'alt_meanonly': True}}],
}


def selt(scale):
    return pd.DataFrame({'EventId': [1, 1, 2, 2], 'SummaryId': [1, 1, 1, 1], 'SampleId': [-1, 1, -1, 1],
                         'Loss': [10.0 * scale, 12.0 * scale, 5.0 * scale, 6.0 * scale]})


def analysis(id, name, status='RUN_COMPLETED'):
    return {'id': id, 'name': name, 'portfolio': 1, 'model': 1, 'status': status,
            'settings': f'/analyses/{id}/settings/', 'modified': '2026-01-01T00:00:00Z',
            'input_file': f'/analyses/{id}/input_file/', 'output_file': f'/analyses/{id}/output_file/'}


@pytest.fixture(autouse=True)
def scenarios_config(monkeypatch):
    monkeypatch.setenv('OASIS_UI_CONFIG', 'scenarios/ui-config.json')


@pytest.fixture
def client():
    client = m.MockApiClient(
        portfolios=[{'id': 1, 'name': 'piwind-small', 'location_file': {'stored': 'l.csv'}, 'accounts_file': None},
                    {'id': 2, 'name': 'unmapped-portfolio', 'location_file': {'stored': 'u.csv'}}],
        models=[{'id': 1, 'model_id': 'PiWind', 'supplier_id': 'OasisLMF', 'version_id': 'v2', 'run_mode': 'V2'},
                {'id': 2, 'model_id': 'NotAScenario', 'supplier_id': 'X', 'version_id': 'v1', 'run_mode': 'V2'}],
        analyses=[analysis(1, 'PiWind – piwind-small [showcase]'),
                  analysis(2, f'My earlier run [v:{VID}]'),
                  analysis(3, f'Someone else [v:{OTHER}]'),
                  analysis(4, 'Standard UI analysis')])
    client.portfolios.location_file.files[1] = pd.DataFrame({
        'LocNumber': ['1', '2'], 'CountryCode': ['GB', 'GB'], 'Latitude': [52.1, 52.2],
        'Longitude': [-1.1, -1.2], 'BuildingTIV': [1000.0, 2000.0], 'LocPerilsCovered': ['WTC', 'WTC']})
    client.models.settings.data[1] = {'name': 'Oasis test European wind model - Paris',
                                      'description': 'PiWind test model'}
    for i in (1, 2, 3):
        client.analyses.settings.data[i] = SETTINGS
        client.analyses.output_file.files[i] = {
            'gul_S1_selt.csv': selt(i),
            'gul_S1_altmeanonly.csv': pd.DataFrame({'SummaryId': [1], 'SampleType': [1], 'MeanLoss': [100.0 * i]})}
        client.analyses.input_file.files[i] = {'location.csv': client.portfolios.location_file.files[1]}
    return client


def app(client, page=None, vid=VID, state=None):
    at = AppTest.from_file('scenarios_app.py', default_timeout=30)
    at.session_state['client_interface'] = ClientInterface(client=client)
    at.query_params['v'] = vid
    for k, v in (state or {}).items():
        at.session_state[k] = v
    if page:
        at.switch_page(page)
    return at.run()


##########################################################################################
# modules.scenarios
##########################################################################################

def test_tags_and_display_names():
    assert sc.display_name('Flood [showcase]') == 'Flood'
    assert sc.display_name(f'My run [v:{VID}]') == 'My run'
    assert sc.display_name('Plain name') == 'Plain name'
    assert sc.tagged_name('Run', sc.visitor_tag(VID)) == f'Run [v:{VID}]'


def test_visitor_and_showcase_filters(client):
    analyses = client.analyses.json_data
    limits = sc.ScenarioLimits()
    assert [a['id'] for a in sc.visitor_analyses(analyses, VID)] == [2]
    assert [a['id'] for a in sc.showcase_analyses(analyses, limits)] == [1]


def test_limits_from_config():
    config = type('C', (), {'scenarios': {'max_samples': 20, 'default_samples': 50, 'unknown': 1}})()
    limits = sc.ScenarioLimits.from_config(config)
    assert limits.max_samples == 20
    assert limits.default_samples == 20  # capped at max_samples


def test_run_blocked_reason():
    limits = sc.ScenarioLimits(max_active_runs_per_visitor=2, max_active_runs=3)
    mine = [analysis(i, f'r [v:{VID}]', 'RUN_STARTED') for i in (1, 2)]
    others = [analysis(i, f'r [v:{OTHER}]', 'RUN_QUEUED') for i in (3, 4)]
    assert sc.run_blocked_reason(mine[:1], VID, limits) is None
    assert 'in progress' in sc.run_blocked_reason(mine, VID, limits)
    assert 'busy' in sc.run_blocked_reason(mine[:1] + others, VID, limits)
    # Another visitor's limit doesn't block me
    assert sc.run_blocked_reason(others[:1], VID, limits) is None


def test_run_settings_apply_choices(client):
    from scenarios_ui.common import run_settings
    ci = ClientInterface(client=client)
    client.models.setting_templates.data[1] = [{'id': 5}]
    client.models.setting_templates.content.data[1] = {
        'model_name_id': 'Old', 'gul_output': True, 'il_output': False,
        'gul_summaries': [{'id': 1, 'ord_output': {'elt_sample': True}, 'oed_fields': ['PortNumber']}]}
    model = client.models.json_data[0]

    settings = run_settings(ci, model, 25, ['LocNumber'])
    assert settings['model_name_id'] == 'PiWind'
    assert settings['number_of_samples'] == 25
    assert settings['join_summary_info'] is True
    assert settings['gul_summaries'][0]['oed_fields'] == ['LocNumber']

    settings = run_settings(ci, model, 10, [])
    assert 'oed_fields' not in settings['gul_summaries'][0]


##########################################################################################
# App
##########################################################################################

def test_explore_lists_only_mapped_scenarios(client):
    at = app(client)
    assert not at.exception, [e.value for e in at.exception]
    assert at.title[0].value == 'Run a scenario'
    choose = [b for b in at.button if b.label == 'Choose this scenario']
    assert len(choose) == 1  # NotAScenario has no portfolio in model_map


def test_my_runs_are_isolated(client):
    at = app(client)
    runs = at.dataframe[-1].value
    assert list(runs['Run']) == ['My earlier run']  # not the showcase, other visitors' or standard runs


def test_run_a_scenario(client):
    at = app(client, state={'sc_model_id': 1})
    assert not at.exception, [e.value for e in at.exception]
    assert 'Check the exposure' in [h.value for h in at.header][1]
    assert at.slider[0].max == 50

    at.button_group[0].set_value(['Location'])
    at.slider[0].set_value(20)
    at.run()
    [b for b in at.button if b.label == 'Run scenario'][0].click().run()

    assert not at.exception, [e.value for e in at.exception]
    created = client.analyses.json_data[-1]
    assert created['name'].endswith(f'[v:{VID}]')
    assert created['portfolio'] == 1 and created['model'] == 1
    assert created['status'] == 'INPUTS_GENERATION_QUEUED'
    settings = client.analyses.settings.data[created['id']]
    assert settings['number_of_samples'] == 20
    assert all(level['oed_fields'] == ['LocNumber'] for level in settings['gul_summaries'])


def test_run_blocked_at_visitor_limit(client):
    for i in (10, 11):
        client.analyses.json_data.append(analysis(i, f'busy [v:{VID}]', 'RUN_STARTED'))
    at = app(client, state={'sc_model_id': 1})
    run = [b for b in at.button if b.label == 'Run scenario'][0]
    assert run.disabled
    assert any('in progress' in i.value for i in at.info)


def test_showcase_page(client):
    at = app(client, 'scenarios_ui/showcase.py')
    assert not at.exception, [e.value for e in at.exception]
    assert at.selectbox[0].options == ['PiWind – piwind-small']
    assert at.subheader[0].value == 'PiWind – piwind-small'


def test_compare_offers_own_and_showcase_runs(client):
    at = app(client, 'scenarios_ui/compare.py')
    assert not at.exception, [e.value for e in at.exception]
    assert at.selectbox[0].options == ['My earlier run (your run)', 'PiWind – piwind-small (showcase)']

    showcase, mine = client.analyses.json_data[0], client.analyses.json_data[1]
    at.selectbox[0].set_value(mine)
    at.selectbox[1].set_value(showcase)
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    assert len(at.get('plotly_chart')) >= 1


def test_guide_page(client):
    at = app(client, 'scenarios_ui/guide.py')
    assert not at.exception
    assert at.title[0].value == 'Guide'


@pytest.mark.parametrize('page', ['pages/portfolios.py', 'pages/analyses.py', 'pages/models.py'])
def test_standard_ui_pages_are_not_reachable(client, page):
    '''st.navigation only registers the Scenarios pages: asking for a standard UI
    page (with uploads/deletes) falls back to the default Scenarios page.'''
    at = app(client)
    at.switch_page(page).run()
    assert not at.exception
    assert [t.value for t in at.title] == ['Run a scenario']
