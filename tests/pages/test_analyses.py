from streamlit.testing.v1 import AppTest
import pandas as pd
from pandas.testing import assert_frame_equal
import tests.mocks as m

from modules.client import ClientInterface

def test_empty_analyses_page():
    at = AppTest.from_file("app.py")
    at.session_state["client"]  = m.MockApiClient()
    at.session_state["client_interface"] = ClientInterface(m.MockApiClient())
    at.switch_page("pages/analyses.py")
    at = at.run()

    # Empty portfolios
    portfolios_df = at.dataframe[0].value
    columns=['id', 'name', 'created', 'modified']
    expected_df = pd.DataFrame(columns=columns)

    assert_frame_equal(expected_df, portfolios_df)

    assert at.tabs[0].label == 'Show Portfolios'
    assert at.tabs[1].label == 'Create Portfolio'

    # Empty analyses
    analysis_df = at.dataframe[1].value
    columns = ["id", "name", "portfolio", "model", "created", "modified", "status"]
    expected_df = pd.DataFrame(columns=columns)
    assert_frame_equal(expected_df, analysis_df)

    assert at.tabs[2].label == 'Run Analysis'
    assert at.tabs[3].label == 'Create Analysis'

def test_display_portfolio(mock_app_test, request):
    config = request.config
    at = mock_app_test
    _portfolio_data = config.portfolios_data[0]

    df_data = {
        'id' : [config.portfolio_ID],
        'name': [_portfolio_data['name']],
        "created": [_portfolio_data['created']],
        "modified": [_portfolio_data['modified']],
        "storage_links": [_portfolio_data['storage_links']]
    }

    expected_df = pd.DataFrame.from_dict(df_data)
    expected_df['created'] = pd.to_datetime(expected_df['created'])
    expected_df['modified'] = pd.to_datetime(expected_df['modified'])
    app_df = at.dataframe[0].value

    assert_frame_equal(expected_df, app_df)

def test_display_analyses(mock_app_test, request):
    at = mock_app_test
    _analyses_data = request.config.analyses_data[0]

    expected_data = {
        "created": [_analyses_data['created']],
        "modified": [_analyses_data['modified']],
        "name": [_analyses_data['name']],
        "id": [request.config.analyses_ID],
        "portfolio": [request.config.portfolio_ID],
        "model": [request.config.model_ID],
        "status": [_analyses_data['status']],
    }

    expected_df = pd.DataFrame.from_dict(expected_data)
    expected_df['created'] = pd.to_datetime(expected_df['created'])
    expected_df['modified'] = pd.to_datetime(expected_df['modified'])

    app_df = at.dataframe[1].value
    assert_frame_equal(expected_df, app_df)

def test_create_portfolio_form(mock_app_test):
    at = mock_app_test

    _portfolio_data = {
        'name': 'new-string',
    }

    at = at.tabs[1].button[0].click().run()

    assert 'Name' in at.error[0].value

    at = at.text_input(key='portfolio_name').input(_portfolio_data['name']).run()
    at = at.tabs[1].button[0].click().run()

    assert at.dataframe[0].value['name'][0] == _portfolio_data['name']
    assert at.success[0].value == 'Successfully created portfolio'


def test_create_analyses_form(mock_app_test, request):
    at = mock_app_test

    portfolio_select = at.tabs[3].selectbox[0].options
    assert len(portfolio_select) == len(request.config.portfolios_data)
    assert request.config.portfolios_data[0]['name'] in portfolio_select[0]

    model_select = at.tabs[3].selectbox[1].options
    assert len(model_select) == len(request.config.models_data)
    assert request.config.models_data[0]['supplier_id'] in model_select[0]
