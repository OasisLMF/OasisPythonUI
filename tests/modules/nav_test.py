"""
Test file for modules/nav.py
"""
import pytest
from streamlit.testing.v1 import AppTest
from tests.modules.mocks import mock_uiconfig, mock_pagelink

from unittest.mock import call

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
