"""
Test file for modules/client.py
"""
from modules.client import ClientInterface
from tests.modules.mocks import mock_client_class, mock_client_instance, ANALYSES, PORTFOLIOS, MODELS

def test_create_client_interface(mock_client_class):
    ci = ClientInterface(username='user', password='password')

    assert ci.portfolios.get() == PORTFOLIOS
    assert ci.models.get() == MODELS
    assert ci.analyses.get() == ANALYSES
