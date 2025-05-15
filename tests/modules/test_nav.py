"""
Test file for modules/nav.py
"""
import json
import pytest
from streamlit.testing.v1 import AppTest

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
    mock_pl = mocker.patch('streamlit.page_link')
    return mock_pl

"""Creating a sidebar with a basic config."""
def app_script():
    from modules.nav import SidebarNav

    SidebarNav()

def test_prelogin_sidebarnav(mock_uiconfig, mock_pagelink):
    at = AppTest.from_function(app_script)
    at.run()

    assert mock_pagelink.call_count == 1
    assert mock_pagelink.call_args[0][0] == 'app.py'
    assert mock_pagelink.call_args[1]['label'] == 'Login'


def test_postlogin_sidebarnav(mock_uiconfig, mock_pagelink):
    at = AppTest.from_function(app_script)
    at.session_state['client'] = True
    at.run()

    assert mock_pagelink.call_count == 2
    assert mock_pagelink.call_args_list[0][0][0] == 'pages/test_1.py'
    assert mock_pagelink.call_args_list[1][0][0] == 'pages/test_2.py'
    assert mock_pagelink.call_args_list[0][1]['label'] == 'Test_1'
    assert mock_pagelink.call_args_list[1][1]['label'] == 'Test_2'
