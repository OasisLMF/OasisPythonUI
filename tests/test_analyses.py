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
def mock_api_client():
    portfolio_ID = 2
    model_ID = 1
    analyses_ID = 2
    portfolios_resp = [{
        'id' : portfolio_ID,
        'name': 'string',
        "created": "2023-05-26T06:48:52.524821Z",
        "modified": "2023-05-26T06:48:52.524821Z",
        "storage_links": f"http://localhost:8000/v1/portfolios/{portfolio_ID}/storage_links/"
    }]

    analyses_resp = [
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
    return MockApiClient(portfolios=portfolios_resp, analyses=analyses_resp)

def test_empty_analyses_page():
    at = AppTest.from_file("app.py")
    at.session_state["client"]  = MockApiClient()
    at.switch_page("pages/analyses.py")
    at = at.run()

    # Empty portfolios
    portfolios_df = at.dataframe[0].value
    columns=['id', 'name', 'created', 'modified', 'storage_links']
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

def test_display_portfolio(mock_api_client):
    at = AppTest.from_file("app.py")
    at.session_state["client"]  = mock_api_client
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

def test_display_analyses(mock_api_client):
    at = AppTest.from_file("app.py")
    at.session_state["client"]  = mock_api_client
    at.switch_page("pages/analyses.py")
    at.run()

    portfolio_ID = 2
    model_ID = 1
    analyses_ID = 2

    expected_data = {
        "created": ["2023-05-26T07:11:08.140539Z",],
        "modified": ["2023-05-26T07:11:08.140539Z",],
        "name": ["string",],
        "id": [analyses_ID],
        "portfolio": [portfolio_ID],
        "model": [model_ID],
        "status": ["NEW",],
    }

    expected_df = pd.DataFrame.from_dict(expected_data)
    expected_df['created'] = pd.to_datetime(expected_df['created'])
    expected_df['modified'] = pd.to_datetime(expected_df['modified'])

    app_df = at.dataframe[1].value
    assert_frame_equal(expected_df, app_df)
