import pandas as pd

class EndpointInterface:
    def __init__(self, client, endpoint_name='portfolios'):
        self.client = client
        self.endpoint_name = endpoint_name

    def get(self, ID=None, df=False):
        data = getattr(self.client, self.endpoint_name).get(ID=ID).json()
        if df:
            data = pd.json_normalize(data)
        return data

class ClientInterface:
    def __init__(self, client):
        self.portfolios = EndpointInterface(client, "portfolios")
        self.analyses = EndpointInterface(client, "analyses")
        self.models = EndpointInterface(client, "models")
        self.client = client

    def create_analysis(self, portfolio_id, model_id, analysis_name):
        resp = self.client.create_analysis(portfolio_id = portfolio_id,
                                    model_id = model_id,
                                    analysis_name = analysis_name)

        return resp
