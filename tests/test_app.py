from streamlit.testing.v1 import AppTest
import pytest

@pytest.fixture()
def app_tester():
    return AppTest.from_file("app.py").run()

def test_login_form_labels(app_tester):
    at = app_tester

    assert at.text_input(key="username").label == "Username"
    assert at.text_input(key="password").label == "Password"

@pytest.mark.parametrize("user, password, err_fragment",
                         [("", "", "Username"),
                          ("TestUser", "", "Password"),
                          ("", "TestPassword", "Username")])
def test_login_validation(app_tester, user, password, err_fragment):
    at = app_tester
    at.text_input(key="username").set_value(user).run()
    at.text_input(key="password").set_value(password).run()

    at.button[0].click().run()
    assert err_fragment in at.error[0].value
