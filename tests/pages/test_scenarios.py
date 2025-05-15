"""
Test file for pages/scenarios.py
"""
import pytest
from streamlit.testing.v1 import AppTest
from tests.modules.mocks import mock_client_instance, mock_pagelink

def test_scenarios(mock_client_instance, mock_pagelink):
    at = AppTest.from_file("pages/scenarios.py")
    at.session_state['client'] = mock_client_instance
    at.run()

    assert not at.exception
