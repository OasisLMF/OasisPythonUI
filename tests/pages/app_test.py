from streamlit.testing.v1 import AppTest
import pytest
from oasis_data_manager.errors import OasisException

@pytest.fixture(autouse=True)
def no_requests(monkeypatch):
    """Remove requests.sessions.Session.request for all tests."""
    monkeypatch.delattr("requests.sessions.Session.request")

@pytest.fixture()
def at_before_login():
    return AppTest.from_file("app.py").run()

def test_login_form_labels(at_before_login):
    at = at_before_login
    assert at.text_input(key="username").label == "Username"
    assert at.text_input(key="password").label == "Password"

@pytest.mark.parametrize("user, password, err_fragment",
                         [("", "", "Username"),
                          ("TestUser", "", "Password"),
                          ("", "TestPassword", "Username")])
def test_login_validation(at_before_login, user, password, err_fragment):
    at = at_before_login
    at.text_input(key="username").set_value(user).run()
    at.text_input(key="password").set_value(password).run()

    at.button[0].click().run()
    assert err_fragment in at.error[0].value

@pytest.fixture
def mock_api_client(mocker):
    class MockJsonObject:
        @staticmethod
        def json():
            return {}

    class MockApiClient:
        valid_user = "mock_user"
        valid_password = "mock_password"

        def __init__(self, username="", password="", api_url=""):
            if username != self.valid_user or password != self.valid_password:
                raise OasisException("")
            return None

        @staticmethod
        def server_info():
            return MockJsonObject
    return mocker.patch("modules.client.APIClient", MockApiClient)

@pytest.mark.parametrize("user, password, errors",
                          [("mock_user", "mock_password", ()),
                          ("incorrect_user", "incorrect_password", ("Authentication Failed",))])
def test_login_authentication(at_before_login, mock_api_client,
                              user, password, errors):
    at = at_before_login

    at.text_input(key="username").set_value(user).run()
    at.text_input(key="password").set_value(password).run()

    at.button[0].click().run()
    assert len(at.error) == len(errors)
    if len(errors) == 1:
        assert at.error[0].value == "Authentication Failed"
