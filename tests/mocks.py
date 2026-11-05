from copy import deepcopy

from requests import Response
from requests.exceptions import HTTPError

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

    def __getattr__(self, name):
        # Any `<x>_file` sub-endpoint is created on first use
        if name.endswith('_file'):
            endpoint = MockFileEndpoint()
            setattr(self, name, endpoint)
            return endpoint
        raise AttributeError(name)

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

    def update(self, ID, name):
        self._find(ID)['name'] = name
        return MockJsonObject(self._find(ID))

    # Analysis actions record the requested transition
    def _set_status(self, ID, status):
        self._find(ID)['status'] = status
        return MockJsonObject(self._find(ID))

    def generate_and_run(self, ID):
        return self._set_status(ID, 'INPUTS_GENERATION_QUEUED')

    def run(self, ID):
        return self._set_status(ID, 'RUN_QUEUED')

    def cancel(self, ID):
        return self._set_status(ID, 'RUN_CANCELLED')


class MockFileEndpoint:
    '''File sub-endpoint (e.g. `portfolios.location_file`) holding DataFrames by ID.

    Missing files raise a 404 `HTTPError`, as the API does.
    '''
    def __init__(self):
        self.files = {}

    def _missing(self, ID):
        response = Response()
        response.status_code = 404
        return HTTPError(f'404: no file for {ID}', response=response)

    def get(self, ID):
        if ID not in self.files:
            raise self._missing(ID)
        return MockText(self.files[ID].to_csv(index=False))

    def get_dataframe(self, ID):
        if ID not in self.files:
            raise self._missing(ID)
        return self.files[ID]


class MockText:
    def __init__(self, text):
        self.text = text


class MockSubEndpoint:
    '''Sub-endpoint (e.g. `analyses.settings`) keyed by parent ID.'''
    def __init__(self, data=None, missing=None):
        self.data = {} if data is None else data
        self.missing = {} if missing is None else missing

    def get(self, ID=None, *args):
        return MockJsonObject(self.data.get(ID, self.missing))

    def post(self, ID, data):
        self.data[ID] = data
        return MockJsonObject(data)


class MockModelsEndpoint(MockEndpoint):
    def __init__(self, json_data=None):
        super().__init__(json_data)
        # No settings templates by default: `get` returns an empty list
        self.setting_templates = MockSubEndpoint(missing=[])
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

    def create_analysis(self, portfolio_id, model_id, analysis_name=None, **kwargs):
        analyses = self.analyses.json_data
        analysis = {'id': max([a['id'] for a in analyses] + [0]) + 1, 'name': analysis_name,
                    'portfolio': portfolio_id, 'model': model_id, 'status': 'NEW', 'settings': None}
        analyses.append(analysis)
        return analysis

    def upload_settings(self, analysis_id, settings):
        self.analyses.settings.post(analysis_id, settings)
        self.analyses._find(analysis_id)['settings'] = f'/analyses/{analysis_id}/settings/'

    def upload_inputs(self, portfolio_name=None, **kwargs):
        if portfolio_name is None:
            raise OasisException('Portfolio name required')

        portfolios = self.portfolios.json_data
        next_id = max([p.get('id', 0) for p in portfolios] + [0]) + 1
        portfolio = {'id': next_id, 'name': portfolio_name}
        portfolios.append(portfolio)
        return portfolio
