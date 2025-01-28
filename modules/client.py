import pandas as pd
from oasislmf.platform_api.client import APIClient
import tempfile
import os
import streamlit as st

class EndpointInterface:
    def __init__(self, client, endpoint_name='portfolios'):
        self.endpoint = getattr(client, endpoint_name)

    def get(self, ID=None, df=False):
        data = self.endpoint.get(ID=ID).json()
        if df:
            data = pd.json_normalize(data)
        return data

    def get_file(self, ID, filename, df=False):
        data = getattr(self.endpoint, filename, None)
        if data is None:
            return data
        if df:
            data = data.get_dataframe(ID)
        else:
            data = data.get(ID)
        return data


class PortfoliosEndpointInterface(EndpointInterface):
    def __init__(self, client):
        super().__init__(client, "portfolios")

    def get_location_file(self, ID, df=False):
        return self.get_file(ID, "location_file", df)

    def get_accounts_file(self, ID, df=False):
        return self.get_file(ID, "accounts_file", df)

    def get_reinsurance_info_file(self, ID, df=False):
        return self.get_file(ID, "reinsurance_info_file", df)

    def get_reinsurance_scope_file(self, ID, df=False):
        return self.get_file(ID, "reinsurance_scope_file", df)


class ClientInterface:
    def __init__(self, client=None, username=None, password=None):
        api_url = os.environ.get('API_URL', 'http://localhost:8000')

        if username is not None and password is not None:
            client = APIClient(username=username, password=password, api_url=api_url)

        assert client is not None, 'Client not set'

        self.client = client
        self.portfolios = PortfoliosEndpointInterface(client)
        self.analyses = EndpointInterface(client, "analyses")
        self.models = EndpointInterface(client, "models")


    def create_analysis(self, portfolio_id, model_id, analysis_name):
        resp = self.client.create_analysis(portfolio_id = portfolio_id,
                                    model_id = model_id,
                                    analysis_name = analysis_name)

        return resp

    def create_and_generate_analysis(self, portfolio_id, model_id, analysis_name):
        resp = self.create_analysis(portfolio_id, model_id, analysis_name)
        resp = self.client.run_generate(resp["id"])
        return resp

    def upload_settings(self, analysis_id, analysis_settings):
        self.client.upload_settings(analysis_id, analysis_settings)

    def run(self, analysis_id):
        return self.client.analyses.run(analysis_id)

    def generate_and_run(self, analysis_id):
        return self.client.analyses.generate_and_run(analysis_id)

    def download_output(self, analysis_id):
        with tempfile.TemporaryDirectory() as tmpdir:
            self.client.download_output(analysis_id, download_path=tmpdir)
            fname = os.listdir(tmpdir)[0]
            with open(os.path.join(tmpdir, fname), 'rb') as f:
                data = f.read()
        return data
