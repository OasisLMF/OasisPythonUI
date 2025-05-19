"""
Test file for pages/scenarios.py
"""
import pytest
from streamlit.testing.v1 import AppTest
from tests.modules.mocks import mock_client_instance, mock_pagelink, mock_client_class
import json
import pandas as pd
from pandas.testing import assert_frame_equal

with open('tests/data/portfolios_test_response.json', 'r') as f:
    PORTFOLIOS = pd.DataFrame(json.load(f))

with open('tests/data/analyses_test_response.json', 'r') as f:
    ANALYSES = pd.DataFrame(json.load(f))

with open('tests/data/models_test_response.json', 'r') as f:
    MODELS = pd.DataFrame(json.load(f))


def test_scenarios_basic_view(mock_client_class, mock_pagelink):
    at = AppTest.from_file("pages/scenarios.py")
    at.run()
    assert not at.exception

    model_view = at.dataframe[0]

    assert model_view.column_order == ['model_id', 'supplier_id']
    assert model_view.selection_mode == [0]
    assert_frame_equal(model_view.value, MODELS)

    column_config = {
        'model_id': {'label': 'Model ID'},
        'supplier_id': {'label': 'Supplier ID'}
    }

    columns = json.loads(model_view.columns)

    for col in column_config:
        for k, v in column_config[col].items():
            assert columns[col][k] == v

    breakpoint()

