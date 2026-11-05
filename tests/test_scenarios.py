'''
Smoke tests for the Scenarios UI pages (Scenarios, Comparison, User Guide),
run with the Scenarios UI config.
'''
import pandas as pd
import pytest

import tests.mocks as m
from tests.conftest import page_app

SETTINGS = {
    'model_supplier_id': 'OasisLMF', 'model_name_id': 'PiWind', 'number_of_samples': 10,
    'gul_output': True,
    'gul_summaries': [{'id': 1, 'ord_output': {'elt_sample': True, 'alt_meanonly': True}}],
}


def selt(scale):
    return pd.DataFrame({'EventId': [1, 1, 2, 2], 'SummaryId': [1, 1, 1, 1], 'SampleId': [-1, 1, -1, 1],
                         'Loss': [10.0 * scale, 12.0 * scale, 5.0 * scale, 6.0 * scale]})


def altmeanonly(scale):
    return pd.DataFrame({'SummaryId': [1], 'SampleType': [1], 'MeanLoss': [100.0 * scale]})


@pytest.fixture(autouse=True)
def scenarios_config(monkeypatch):
    monkeypatch.setenv('OASIS_UI_CONFIG', 'scenarios/ui-config.json')


@pytest.fixture
def client():
    analyses = [{'id': i, 'name': f'run {i}', 'portfolio': 1, 'model': 1, 'status': 'RUN_COMPLETED',
                 'settings': f'/analyses/{i}/settings/', 'output_file': f'/analyses/{i}/output_file/',
                 'input_file': f'/analyses/{i}/input_file/', 'modified': '2026-01-01T00:00:00Z'}
                for i in (1, 2)]
    client = m.MockApiClient(
        portfolios=[{'id': 1, 'name': 'piwind-small', 'location_file': {'stored': 'l.csv'},
                     'accounts_file': None}],
        models=[{'id': 1, 'model_id': 'PiWind', 'supplier_id': 'OasisLMF', 'version_id': 'v2',
                 'run_mode': 'V2'}],
        analyses=analyses)
    client.portfolios.location_file.files[1] = pd.DataFrame({
        'LocNumber': ['1'], 'Latitude': [48.8], 'Longitude': [2.3], 'BuildingTIV': [1000.0], 'CountryCode': ['FR']})
    client.models.settings.data[1] = {'name': 'Oasis test European wind model - Paris',
                                      'description': 'PiWind test model'}
    for i, scale in [(1, 1), (2, 2)]:
        client.analyses.settings.data[i] = SETTINGS
        client.analyses.input_file.files[i] = {'location.csv': client.portfolios.location_file.files[1]}
        client.analyses.output_file.files[i] = {'gul_S1_selt.csv': selt(scale),
                                                'gul_S1_altmeanonly.csv': altmeanonly(scale)}
    return client


def test_scenarios_page(client):
    at = page_app('pages/scenarios.py', client)

    assert not at.exception
    models = at.dataframe[0].value
    assert list(models['model_name']) == ['Oasis test European wind model - Paris']
    assert 'Please select a model.' in [i.value for i in at.info]


def test_comparison_page_requires_two_analyses(client):
    at = page_app('pages/comparison.py', client)

    assert not at.exception
    assert 'Select 2 analyses.' in [i.value for i in at.info]
    assert [s.label for s in at.selectbox][:2] == ['Select Analysis 1', 'Select Analysis 2']


def test_comparison_page_compares_two_analyses(client):
    at = page_app('pages/comparison.py', client)
    assert at.selectbox[0].options == ['run 2', 'run 1']

    first, second = client.analyses.json_data
    at.selectbox[0].set_value(first)
    at.selectbox[1].set_value(second)
    at.run()

    assert not at.exception, [e.value for e in at.exception]
    assert 'Select 2 analyses.' not in [i.value for i in at.info]
    assert [e.label for e in at.expander] == ['Analysis Summary']
    assert len(at.get('plotly_chart')) >= 1  # output comparison rendered


def test_user_guide_page(client):
    at = page_app('pages/scenariosGuide.py', client)
    assert not at.exception
    assert at.title[0].value == 'User Guide: Scenario analysis and comparison'
