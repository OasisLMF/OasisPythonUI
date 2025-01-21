from streamlit.testing.v1 import AppTest
import pytest
from oasis_data_manager.errors import OasisException
import pandas as pd
from pandas.testing import assert_frame_equal

from modules.client import ClientInterface

@pytest.fixture(autouse=True)
def no_requests(monkeypatch):
    """Remove requests.sessions.Session.request for all tests."""
    monkeypatch.delattr("requests.sessions.Session.request")

class MockJsonObject:
    def __init__(self, data = {}):
        self.data = data

    def json(self):
        return self.data

class MockEndpoint:
    def __init__(self, json_data=[{}]):
        self.json_data = json_data

    def get(self, ID=None):
        if ID is None:
            data = self.json_data
        else:
            data = self.json_data[ID]
        return MockJsonObject(data)

class MockApiClient:
    def __init__(self, username="", password="",
                 portfolios=[], models=[], analyses=[]):
        self.portfolios = MockEndpoint(portfolios)
        self.models = MockEndpoint(models)
        self.analyses = MockEndpoint(analyses)

    @staticmethod
    def server_info():
        return MockJsonObject

    def upload_inputs(self, portfolio_name=None,**kwargs):
        if portfolio_name is None:
            raise OasisException('Portfolio name required')

        if len(self.portfolios.json_data) == 1:
            self.portfolios.json_data[0]['name'] = portfolio_name

        else:
            self.portfolios = [
                {
                    'name': portfolio_name
                }
            ]

portfolio_ID = 2
portfolios_data = [{
    'id' : portfolio_ID,
    'name': 'string',
    "created": "2023-05-26T06:48:52.524821Z",
    "modified": "2023-05-26T06:48:52.524821Z",
    "storage_links": f"http://localhost:8000/v1/portfolios/{portfolio_ID}/storage_links/"
}]

model_ID = 1
models_data = [
    {
        'id': model_ID,
        'supplier_id': 'OasisLMF',
        'model_id': 'model',
        'version_id': 'v2',
        "created": "2023-05-26T07:11:08.140539Z",
        "modified": "2023-05-26T07:11:08.140539Z",
    }
]

analyses_ID = 2
analyses_data = [
    {
        "created": "2023-05-26T07:11:08.140539Z",
        "modified": "2023-05-26T07:11:08.140539Z",
        "name": "string",
        "id": analyses_ID,
        "portfolio": portfolio_ID,
        "model": model_ID,
        "status": "NEW",
    }
]
@pytest.fixture()
def mock_api_client():
    return MockApiClient(portfolios=portfolios_data,
                         analyses=analyses_data,
                         models=models_data)

@pytest.fixture()
def mock_client_interface(mock_api_client):
    return ClientInterface(client = mock_api_client)


@pytest.fixture()
def mock_app_test(mock_api_client, mock_client_interface):
    at = AppTest.from_file("app.py")
    at.session_state["client"]  = mock_api_client
    at.session_state["client_interface"] = mock_client_interface
    at.switch_page("pages/analyses.py")
    at.run()
    return at


def test_empty_analyses_page():
    at = AppTest.from_file("app.py")
    at.session_state["client"]  = MockApiClient()
    at.session_state["client_interface"] = ClientInterface(MockApiClient())
    at.switch_page("pages/analyses.py")
    at = at.run()

    # Empty portfolios
    portfolios_df = at.dataframe[0].value
    columns=['id', 'name', 'created', 'modified']
    expected_df = pd.DataFrame(columns=columns)

    assert_frame_equal(expected_df, portfolios_df)

    assert at.tabs[0].label == 'Show Portfolios'
    assert at.tabs[1].label == 'Create Portfolio'

    # Empty analyses
    analysis_df = at.dataframe[1].value
    columns = ["id", "name", "portfolio", "model", "created", "modified", "status"]
    expected_df = pd.DataFrame(columns=columns)
    assert_frame_equal(expected_df, analysis_df)

    assert at.tabs[2].label == 'Run Analysis'
    assert at.tabs[3].label == 'Create Analysis'

def test_display_portfolio(mock_app_test):
    at = mock_app_test
    _portfolio_data = portfolios_data[0]

    df_data = {
        'id' : [portfolio_ID],
        'name': [_portfolio_data['name']],
        "created": [_portfolio_data['created']],
        "modified": [_portfolio_data['modified']],
        "storage_links": [_portfolio_data['storage_links']]
    }

    expected_df = pd.DataFrame.from_dict(df_data)
    expected_df['created'] = pd.to_datetime(expected_df['created'])
    expected_df['modified'] = pd.to_datetime(expected_df['modified'])
    app_df = at.dataframe[0].value

    assert_frame_equal(expected_df, app_df)

def test_display_analyses(mock_app_test):
    at = mock_app_test
    _analyses_data = analyses_data[0]

    expected_data = {
        "created": [_analyses_data['created']],
        "modified": [_analyses_data['modified']],
        "name": [_analyses_data['name']],
        "id": [analyses_ID],
        "portfolio": [portfolio_ID],
        "model": [model_ID],
        "status": [_analyses_data['status']],
    }

    expected_df = pd.DataFrame.from_dict(expected_data)
    expected_df['created'] = pd.to_datetime(expected_df['created'])
    expected_df['modified'] = pd.to_datetime(expected_df['modified'])

    app_df = at.dataframe[1].value
    assert_frame_equal(expected_df, app_df)

def test_create_portfolio_form(mock_app_test):
    at = mock_app_test

    _portfolio_data = {
        'name': 'new-string',
    }

    at = at.tabs[1].button[0].click().run()

    assert 'Name' in at.error[0].value

    at = at.text_input(key='portfolio_name').input(_portfolio_data['name']).run()
    at = at.tabs[1].button[0].click().run()

    assert at.dataframe[0].value['name'][0] == _portfolio_data['name']
    assert at.success[0].value == 'Successfully created portfolio'


def test_create_analyses_form(mock_app_test):
    at = mock_app_test

    portfolio_select = at.tabs[3].selectbox[0].options
    assert len(portfolio_select) == len(portfolios_data)
    assert portfolios_data[0]['name'] in portfolio_select[0]

    model_select = at.tabs[3].selectbox[1].options
    assert len(model_select) == len(models_data)
    assert models_data[0]['supplier_id'] in model_select[0]

    # todo: AppTest does not support selecting dataframes, use alt testing method
