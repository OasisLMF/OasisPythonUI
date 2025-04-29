import pandas as pd
from oasislmf.platform_api.client import APIClient
import tempfile
import os
from requests import HTTPError
import streamlit as st
import logging

logger = logging.getLogger(__name__)


class EndpointInterface:
    def __init__(self, client, endpoint_name='portfolios'):
        self.endpoint = getattr(client, endpoint_name)

    def get(self, ID=None, df=False):
        data = self.endpoint.get(ID=ID).json()
        if df:
            data = pd.json_normalize(data)
        return data

    def search(self, metadata={}):
        return self.endpoint.search(metadata=metadata).json()

    def get_file(self, ID, filename, df=False):
        file_available = self.get(ID).get(filename, None)
        if file_available is None:
            logger.error(f'File not available. Analysis ID: {ID }Filename: {filename}')
            return None

        data = getattr(self.endpoint, filename)
        if df:
            data = data.get_dataframe(ID)
        else:
            data = data.get(ID)
        return data

class AnalysesEndpointInterface(EndpointInterface):
    def __init__(self, client):
        super().__init__(client, endpoint_name='analyses')

    def get_traceback(self, ID, error_type='input_generation'):
        '''
        Get the contents of the traceback file if it exists

        Parameters
        ----------
        ID : int
             Analysis id.
        error_type : str
                     `input_generation` or `run`.

        Returns
        -------
        `str` contents of traceback file or `None` if the file does not exist.
        '''
        traceback_endpoint = error_type + '_traceback_file'

        try:
            return getattr(self.endpoint, traceback_endpoint).get(ID).text
        except HTTPError as e:
            logger.error(e)
            return None


class PortfoliosEndpointInterface(EndpointInterface):
    def __init__(self, client):
        super().__init__(client, "portfolios")
        self.client = client

    def get_location_file(self, ID, df=False):
        return self.get_file(ID, "location_file", df)

    def get_accounts_file(self, ID, df=False):
        return self.get_file(ID, "accounts_file", df)

    def get_reinsurance_info_file(self, ID, df=False):
        return self.get_file(ID, "reinsurance_info_file", df)

    def get_reinsurance_scope_file(self, ID, df=False):
        return self.get_file(ID, "reinsurance_scope_file", df)

    def create(self, name, location_file = None, accounts_file = None,
               reinsurance_info_file = None, reinsurance_scope_file = None):
        '''
        Create a portfolio using the `UploadedFile` objects created when using the `st.file_uploader`.

        Parameters
        ----------
        name : str
               Name for the assigned portfolio
        location_file : UploadedFile
        accounts_file : UploadedFile
        reinsurance_scope_file : UploadedFile
        reinsurance_scope_file : UploadedFile
        '''

        def prepare_upload_f(fname, fbytes):
            if fbytes is None:
                return None
            return {'name': fname, 'bytes': fbytes}

        location_f = prepare_upload_f('location_file', location_file)
        accounts_f = prepare_upload_f('accounts_file', accounts_file)
        ri_info_f = prepare_upload_f('reinsurance_info_file', reinsurance_info_file)
        ri_scope_f= prepare_upload_f('reinsurance_scope_file', reinsurance_scope_file)

        self.client.upload_inputs(portfolio_name = name,
                             location_f = location_f,
                             accounts_f = accounts_f,
                             ri_info_f = ri_info_f,
                             ri_scope_f = ri_scope_f)



class ClientInterface:
    def __init__(self, client=None, username=None, password=None):
        api_url = os.environ.get('API_URL', 'http://localhost:8000')

        if username is not None and password is not None:
            client = APIClient(username=username, password=password, api_url=api_url)

        assert client is not None, 'Client not set'

        self.client = client
        self.portfolios = PortfoliosEndpointInterface(client)
        self.analyses = AnalysesEndpointInterface(client)
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
