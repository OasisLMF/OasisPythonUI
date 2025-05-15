"""
Test file for modules/nav.py
"""
import pytest
from streamlit.testing.v1 import AppTest

from unittest.mock import call

@pytest.fixture
def mock_uiconfig(mocker):
    mocked_uiconfig = mocker.mock_open(read_data='''
    {
        "pages" : [{"path": "pages/test_1.py", "label": "Test_1"},
                   {"path": "pages/test_2.py", "label": "Test_2"}
        ],
        "post_login_page": "pages/test.py"
    }''')

    original_open = open

    def open_side_effect(file, mode='r', *args, **kwargs):
        if file == "ui-config.json":
            return mocked_uiconfig(file, mode, *args, **kwargs)
        return original_open(file, mode, *args, **kwargs)
    mocker.patch('builtins.open', side_effect=open_side_effect)

@pytest.fixture
def mock_pagelink(mocker):
    mock_pl = mocker.patch('streamlit.page_link', autospec=True)
    return mock_pl

"""Creating a sidebar with a basic config."""
def app_script():
    from modules.nav import SidebarNav
    SidebarNav()

def test_prelogin_sidebarnav(mock_uiconfig, mock_pagelink):
    at = AppTest.from_function(app_script)
    at.run()

    assert not at.exception
    assert mock_pagelink.call_count == 1
    mock_pagelink.assert_called_with('app.py', label='Login')


def test_postlogin_sidebarnav(mock_uiconfig, mock_pagelink):
    at = AppTest.from_function(app_script)
    at.session_state['client'] = True
    at.run()

    assert not at.exception
    assert mock_pagelink.call_count == 2
    expected_calls = (call('pages/test_1.py', label='Test_1'),
                      call('pages/test_2.py', label='Test_2'))
    mock_pagelink.assert_has_calls(expected_calls)
