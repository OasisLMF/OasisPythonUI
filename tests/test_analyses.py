from streamlit.testing.v1 import AppTest
import pytest
from oasis_data_manager.errors import OasisException
import pandas as pd
from pandas.testing import assert_frame_equal

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
    def __init__(self, json_data={}):
        self.json_data = json_data

    def get(self):
        return MockJsonObject(self.json_data)

class MockApiClient:
    def __init__(self, username="", password="",
                 portfolios={}, models={}, analyses={}):
        self.portfolios = MockEndpoint(portfolios)
        self.models = MockEndpoint(models)
        self.analyses = MockEndpoint(analyses)

    @staticmethod
    def server_info():
        return MockJsonObject

@pytest.fixture()
def mock_api_client_portfolios():
    ID = 2
    portfolios_resp = [{
        'id' : ID,
        'name': 'string',
        "created": "2023-05-26T06:48:52.524821Z",
        "modified": "2023-05-26T06:48:52.524821Z",
        "storage_links": f"http://localhost:8000/v1/portfolios/{ID}/storage_links/"
    }]
    return MockApiClient(portfolios=portfolios_resp)

@pytest.fixture()
def mock_api_client_empty():
    return MockApiClient()

@pytest.fixture()
def at_analyses(mock_api_client_empty):
    at = AppTest.from_file("app.py")
    at.session_state["client"]  = mock_api_client_empty
    at.switch_page("pages/analyses.py")
    return at.run()

def test_empty_portfolios(at_analyses):
    at = at_analyses

    # Empty portfolios
    portfolios_df = at.dataframe[0].value
    expected_df = pd.DataFrame(columns=['id', 'name', 'created', 'modified',
                                         'storage_links'])
    assert_frame_equal(expected_df, portfolios_df)

    assert at.tabs[0].label == 'Show Portfolios'
    assert at.tabs[1].label == 'Create Portfolio'

def test_display_portfolio(mock_api_client_portfolios):
    at = AppTest.from_file("app.py")
    at.session_state["client"]  = mock_api_client_portfolios
    at.switch_page("pages/analyses.py")
    at.run()

    ID = 2
    df_data = {
        'id' : [ID],
        'name': ['string'],
        "created": ["2023-05-26T06:48:52.524821Z"],
        "modified": ["2023-05-26T06:48:52.524821Z"],
        "storage_links": [f"http://localhost:8000/v1/portfolios/{ID}/storage_links/"]
    }

    expected_df = pd.DataFrame.from_dict(df_data)
    expected_df['created'] = pd.to_datetime(expected_df['created'])
    expected_df['modified'] = pd.to_datetime(expected_df['modified'])
    app_df = at.dataframe[0].value

    assert_frame_equal(expected_df, app_df)
