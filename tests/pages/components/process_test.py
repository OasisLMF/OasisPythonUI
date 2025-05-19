"""
Test file for pages/components/process.py
"""
from tests.modules.mocks import mock_client_class, mock_client_instance
import pytest
from pages.components.process import enrich_portfolios
import pandas as pd
import json


class TestEnrichPortfolio:
    @pytest.fixture
    def test_portfolio(self):
        with open('tests/data/portfolios_test_response.json', 'r') as f:
            test_portfolio = json.load(f)
        test_portfolio = pd.json_normalize(test_portfolio)
        return test_portfolio

    def test_no_files(self, mock_client_instance, test_portfolio):
        mock_client_instance.portfolios.get_location_file.return_value = None
        mock_client_instance.portfolios.get_accounts_file.return_value = None

        enriched_portfolio = enrich_portfolios(test_portfolio, mock_client_instance)

        assert enriched_portfolio['number_locations'].isna().all()
        assert enriched_portfolio['number_accounts'].isna().all()


    def test_locations(self, mock_client_instance, test_portfolio):
        test_locations = pd.read_csv('tests/data/inputs/location.csv')
        mock_client_instance.portfolios.get_location_file.return_value = test_locations

        enriched_portfolio = enrich_portfolios(test_portfolio, mock_client_instance, disable=['acc'])

        assert enriched_portfolio['number_locations'][0] == 10


    def test_accounts(self, mock_client_instance, test_portfolio):
        test_accounts = pd.read_csv('tests/data/inputs/accounts.csv')
        mock_client_instance.portfolios.get_accounts_file.return_value = test_accounts

        enriched_portfolio = enrich_portfolios(test_portfolio, mock_client_instance, disable=['loc'])

        assert enriched_portfolio['number_accounts'][0] == 2


    def test_disable(self, mock_client_instance, test_portfolio):
        test_locations = pd.read_csv('tests/data/inputs/location.csv')
        mock_client_instance.portfolios.get_location_file.return_value = test_locations
        test_accounts = pd.read_csv('tests/data/inputs/accounts.csv')
        mock_client_instance.portfolios.get_accounts_file.return_value = test_accounts

        enriched_portfolio = enrich_portfolios(test_portfolio, mock_client_instance, disable=['acc'])
        assert "number_locations" in enriched_portfolio.columns
        assert "number_accounts" not in enriched_portfolio.columns

        enriched_portfolio = enrich_portfolios(test_portfolio, mock_client_instance, disable=['loc'])
        assert "number_locations" not in enriched_portfolio.columns
        assert "number_accounts" in enriched_portfolio.columns
