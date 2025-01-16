import pandas as pd
from oasislmf.platform_api.client import APIClient

class EndpointInterface:
    def __init__(self, client, endpoint_name='portfolios'):
        self.endpoint = getattr(client, endpoint_name)

    def get(self, ID=None, df=False):
        data = self.endpoint.get(ID=ID).json()
        if df:
            data = pd.json_normalize(data)
        return data

    def get_file(self, ID, filename, df=False):
        if df:
            data = getattr(self.endpoint, filename).get_dataframe(ID)
        else:
            data = getattr(self.endpoint, filename).get(ID)
        return data

class ClientInterface:
    def __init__(self, client=None, username=None, password=None):
        if username is not None and password is not None:
            client = APIClient(username=username, password=password)

        assert client is not None, 'Client not set'

        self.client = client
        self.portfolios = EndpointInterface(client, "portfolios")
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
