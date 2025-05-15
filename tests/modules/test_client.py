"""
Test file for modules/client.py
"""
import pytest
from modules.client import ClientInterface
from unittest.mock import patch, MagicMock
import requests
import json
from oasislmf.platform_api.client import APIClient

with open('tests/data/portfolios_test_response.json', 'r') as f:
    test_portfolios = json.load(f)

with open('tests/data/analyses_test_response.json', 'r') as f:
    test_analyses = json.load(f)

with open('tests/data/models_test_response.json', 'r') as f:
    test_models = json.load(f)


@pytest.fixture
def mock_client_instance():
    mock_instance = MagicMock()
    mock_instance.portfolios.get.return_value.json.return_value = test_portfolios
    mock_instance.analyses.get.return_value.json.return_value = test_analyses
    mock_instance.models.get.return_value.json.return_value = test_models
    return mock_instance

@pytest.fixture
def mock_client_class(mocker, mock_client_instance):
    mock_client_class = MagicMock(spec_set=APIClient)
    mock_client_class.return_value = mock_client_instance
    mocker.patch('modules.client.APIClient', return_value=mock_client_instance)

def test_create_client_interface(mock_client_class):
    ci = ClientInterface(username='user', password='password')

    assert ci.portfolios.get() == test_portfolios
    assert ci.models.get() == test_models
    assert ci.analyses.get() == test_analyses
