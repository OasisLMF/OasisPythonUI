from copy import deepcopy

from oasis_data_manager.errors import OasisException


class MockJsonObject:
    def __init__(self, data=None):
        self.data = {} if data is None else data

    def json(self):
        return self.data


class MockEndpoint:
    '''Minimal stand-in for an `oasislmf` APIClient endpoint backed by a list of dicts.

    `get(ID)` looks records up by their `id` field (falling back to list
    position for records without one), matching the real API.
    '''
    def __init__(self, json_data=None):
        self.json_data = [] if json_data is None else json_data
        # Sub-endpoints wrapped by `modules.client` interfaces
        self.settings = MockSubEndpoint()

    def _find(self, ID):
        for record in self.json_data:
            if isinstance(record, dict) and record.get('id') == ID:
                return record
        return self.json_data[ID]

    def get(self, ID=None):
        if ID is None:
            return MockJsonObject(self.json_data)
        return MockJsonObject(self._find(ID))

    def search(self, metadata=None):
        metadata = metadata or {}
        matches = [r for r in self.json_data
                   if all(r.get(k) == v for k, v in metadata.items())]
        return MockJsonObject(matches)

    def delete(self, ID):
        self.json_data[:] = [r for r in self.json_data if r.get('id') != ID]


class MockSubEndpoint:
    '''Sub-endpoint (e.g. `analyses.settings`) keyed by parent ID.'''
    def __init__(self, data=None):
        self.data = {} if data is None else data

    def get(self, ID=None):
        return MockJsonObject(self.data.get(ID, {}))


class MockModelsEndpoint(MockEndpoint):
    def __init__(self, json_data=None):
        super().__init__(json_data)
        self.setting_templates = MockSubEndpoint()
        self.setting_templates.content = MockSubEndpoint()


class MockApiClient:
    def __init__(self, username="", password="",
                 portfolios=None, models=None, analyses=None, **kwargs):
        # Copy so tests mutating endpoint data can't leak into shared fixtures
        self.portfolios = MockEndpoint(deepcopy(portfolios))
        self.models = MockModelsEndpoint(deepcopy(models))
        self.analyses = MockEndpoint(deepcopy(analyses))

    @staticmethod
    def server_info():
        return MockJsonObject()

    def upload_inputs(self, portfolio_name=None, **kwargs):
        if portfolio_name is None:
            raise OasisException('Portfolio name required')

        portfolios = self.portfolios.json_data
        next_id = max([p.get('id', 0) for p in portfolios] + [0]) + 1
        portfolios.append({'id': next_id, 'name': portfolio_name})
