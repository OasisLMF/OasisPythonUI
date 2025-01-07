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
    @staticmethod
    def json():
        return {}

class MockEndpoint:
    def get(self):
        return MockJsonObject

class MockApiClient:
    def __init__(self, username="", password=""):
        self.portfolios = MockEndpoint()
        self.models = MockEndpoint()
        self.analyses = MockEndpoint()

    @staticmethod
    def server_info():
        return MockJsonObject

@pytest.fixture
def mock_api_client():
    return MockApiClient()

@pytest.fixture()
def at_analyses(mock_api_client):
    at = AppTest.from_file("app.py")
    at.session_state["client"]  = mock_api_client
    at.switch_page("pages/analyses.py")
    return at.run()

def test_empty_portfolios(at_analyses):
    at = at_analyses

    # Empty portfolios
    portfolios_df = at.dataframe[0].value
    expected_df = pd.DataFrame(columns=['id', 'name', 'created', 'modified',
                                         'storage_links'])
    assert_frame_equal(expected_df, portfolios_df)
