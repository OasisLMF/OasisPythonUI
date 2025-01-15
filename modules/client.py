import pandas as pd
from oasislmf.platform_api.client import APIClient

def get_client(username="admin", password="password"):
    return APIClient(username=username, password=password)

def check_analysis_status(client, id, required_status):
    curr_status = client.analyses.get(id).json()['status']
    return curr_status == required_status

def get_portfolios(client):
    resp = client.portfolios.get().json()
    return pd.json_normalize(resp)

def get_analyses(client):
    analyses = client.analyses.get().json()
    return pd.json_normalize(analyses)

def get_models(client):
    analyses = client.models.get().json()
    return pd.json_normalize(analyses)

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
