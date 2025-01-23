import pytest
from modules.client import ClientInterface
from tests.mocks import MockApiClient
from streamlit.testing.v1 import AppTest

@pytest.fixture(autouse=True)
def no_requests(monkeypatch):
    """Remove requests.sessions.Session.request for all tests."""
    monkeypatch.delattr("requests.sessions.Session.request")


def pytest_configure(config):
    config.portfolio_ID = 2
    config.portfolios_data = [{
        'id' : config.portfolio_ID,
        'name': 'string',
        "created": "2023-05-26T06:48:52.524821Z",
        "modified": "2023-05-26T06:48:52.524821Z",
        "storage_links": f"http://localhost:8000/v1/portfolios/{config.portfolio_ID}/storage_links/"
    }]

    config.model_ID = 1
    config.models_data = [
        {
            'id': config.model_ID,
            'supplier_id': 'OasisLMF',
            'model_id': 'model',
            'version_id': 'v2',
            'run_mode': 'V2',
            "created": "2023-05-26T07:11:08.140539Z",
            "modified": "2023-05-26T07:11:08.140539Z",
        }
    ]

    config.analyses_ID = 2
    config.analyses_data = [
        {
            "created": "2023-05-26T07:11:08.140539Z",
            "modified": "2023-05-26T07:11:08.140539Z",
            "name": "string",
            "id": config.analyses_ID,
            "portfolio": config.portfolio_ID,
            "model": config.model_ID,
            "status": "NEW",
        }
    ]

@pytest.fixture()
def mock_api_client(request):
    config = request.config
    return MockApiClient(portfolios=config.portfolios_data,
                         analyses=config.analyses_data,
                         models=config.models_data)

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

