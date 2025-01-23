from oasis_data_manager.errors import OasisException

class MockJsonObject:
    def __init__(self, data = {}):
        self.data = data

    def json(self):
        return self.data

class MockEndpoint:
    def __init__(self, json_data=[{}]):
        self.json_data = json_data

    def get(self, ID=None):
        if ID is None:
            data = self.json_data
        else:
            data = self.json_data[ID]
        return MockJsonObject(data)

class MockApiClient:
    def __init__(self, username="", password="",
                 portfolios=[], models=[], analyses=[]):
        self.portfolios = MockEndpoint(portfolios)
        self.models = MockEndpoint(models)
        self.analyses = MockEndpoint(analyses)

    @staticmethod
    def server_info():
        return MockJsonObject

    def upload_inputs(self, portfolio_name=None,**kwargs):
        if portfolio_name is None:
            raise OasisException('Portfolio name required')

        if len(self.portfolios.json_data) == 1:
            self.portfolios.json_data[0]['name'] = portfolio_name

        else:
            self.portfolios = [
                {
                    'name': portfolio_name
                }
            ]
