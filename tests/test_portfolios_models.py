import tests.mocks as m
from tests.conftest import page_app

from pages.components.common import SELECTED_MODEL, SELECTED_PORTFOLIO
from pages.components.data import guess_file_type


def test_empty_portfolios_page():
    at = page_app('pages/portfolios.py', m.MockApiClient())
    assert not at.exception
    assert at.title[0].value == 'Portfolios'
    assert 'No portfolios yet. Create one to get started.' in [i.value for i in at.info]


def test_portfolios_table(mock_api_client, request):
    at = page_app('pages/portfolios.py', mock_api_client)
    assert not at.exception

    table = at.dataframe[0].value
    assert list(table['name']) == [request.config.portfolios_data[0]['name']]
    assert bool(table['location_file'].iloc[0]) is True
    assert bool(table['accounts_file'].iloc[0]) is False
    assert table['n_analyses'].iloc[0] == 1


def test_portfolio_detail(mock_api_client, request):
    at = page_app('pages/portfolios.py', mock_api_client,
                  {SELECTED_PORTFOLIO: request.config.portfolio_ID})
    assert not at.exception
    assert at.subheader[0].value == request.config.portfolios_data[0]['name']
    assert [t.label for t in at.tabs] == ['Files', 'Exposure', 'Analyses (1)']


def test_new_portfolio_dialog(mock_api_client):
    at = page_app('pages/portfolios.py', mock_api_client)
    at = at.button[0].click().run()

    assert not at.exception
    assert at.text_input(key='new_portfolio_name').label == 'Portfolio name'
    create = [b for b in at.button if b.label == 'Create portfolio'][0]
    assert create.disabled  # no name or location file yet


def test_rename_portfolio(mock_api_client, request):
    config = request.config
    at = page_app('pages/portfolios.py', mock_api_client, {SELECTED_PORTFOLIO: config.portfolio_ID})

    at.text_input(key=f'rename_{config.portfolio_ID}').input('renamed').run()
    at.button(key=f'rename_save_{config.portfolio_ID}').click().run()

    assert not at.exception
    assert mock_api_client.portfolios.json_data[0]['name'] == 'renamed'


def test_guess_file_type():
    assert guess_file_type('SourceLocOEDPiWind.csv') == 'location_file'
    assert guess_file_type('SourceAccOEDPiWind.csv') == 'accounts_file'
    assert guess_file_type('SourceReinsInfoOEDPiWind.csv') == 'reinsurance_info_file'
    assert guess_file_type('ri_scope.parquet') == 'reinsurance_scope_file'
    assert guess_file_type('exposure.csv') is None


def test_models_page(mock_api_client, request):
    config = request.config
    mock_api_client.models.settings.data[config.model_ID] = {
        'name': 'Friendly model name',
        'description': 'A test model',
        'model_settings': {'event_set': {'name': 'Event Set', 'desc': 'd', 'default': 'p',
                                         'options': [{'id': 'p', 'desc': 'Probabilistic'}]}},
    }
    at = page_app('pages/models.py', mock_api_client, {SELECTED_MODEL: config.model_ID})

    assert not at.exception
    assert list(at.dataframe[0].value['name']) == ['Friendly model name']
    assert at.subheader[0].value == 'Friendly model name'
    assert [t.label for t in at.tabs] == ['Overview', 'Run options', 'Parameters', 'Perils', 'Settings JSON']


def test_model_without_settings(mock_api_client, request):
    at = page_app('pages/models.py', mock_api_client, {SELECTED_MODEL: request.config.model_ID})
    assert not at.exception
    assert 'No model settings have been registered for this model.' in [w.value for w in at.warning]
