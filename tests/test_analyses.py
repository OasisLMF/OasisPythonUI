from streamlit.testing.v1 import AppTest
import tests.mocks as m

from modules.client import ClientInterface


def analyses_app(client):
    at = AppTest.from_file("app.py", default_timeout=30)
    at.session_state["client"] = client
    at.session_state["client_interface"] = ClientInterface(client=client)
    at.switch_page("pages/analyses.py")
    return at.run()


def test_empty_analyses_page():
    at = analyses_app(m.MockApiClient())

    assert not at.exception

    # Empty portfolios table shows only the name column
    portfolios_df = at.dataframe[0].value
    assert portfolios_df.empty
    assert list(portfolios_df.columns) == ['name']
    assert at.button[0].label == 'Create Portfolio'

    assert [t.label for t in at.tabs] == ['Run Analysis', 'Create Analysis']

    info = [i.value for i in at.info]
    assert 'No analyses.' in info
    assert 'Ensure portfolios and models are loaded.' in info


def test_display_portfolio(mock_app_test, request):
    at = mock_app_test

    portfolios_df = at.dataframe[0].value
    expected_names = [p['name'] for p in request.config.portfolios_data]
    assert list(portfolios_df['name']) == expected_names


def test_display_analyses(mock_app_test, request):
    config = request.config
    at = mock_app_test
    analysis = config.analyses_data[0]

    analyses_df = at.dataframe[1].value
    assert len(analyses_df) == 1
    row = analyses_df.iloc[0]

    assert row['id'] == config.analyses_ID
    assert row['name'] == analysis['name']
    assert row['status'] == analysis['status']
    # Enriched from the portfolios / models endpoints
    assert row['portfolio_name'] == config.portfolios_data[0]['name']
    assert row['model_id'] == config.models_data[0]['model_id']
    assert row['model_supplier'] == config.models_data[0]['supplier_id']


def test_create_portfolio_button_opens_dialog(mock_app_test):
    at = mock_app_test

    at = at.button[0].click().run()

    assert not at.exception
    assert at.text_input(key='portfolio_name').label == 'Portfolio Name'


def test_create_portfolio_form_requires_name():
    at = AppTest.from_file("tests/fixtures/create_portfolio_form_app.py").run()

    at = at.button[0].click().run()

    assert 'Name' in at.error[0].value
    assert 'form_data' not in at.session_state


def test_create_portfolio_form_returns_data():
    at = AppTest.from_file("tests/fixtures/create_portfolio_form_app.py").run()

    at = at.text_input(key='portfolio_name').input('new-portfolio').run()
    at = at.button[0].click().run()

    assert not at.error
    form_data = at.session_state['form_data']
    assert form_data['name'] == 'new-portfolio'
    assert form_data['location_file'] is None


def test_create_analyses_form(mock_app_test, request):
    at = mock_app_test
    create_tab = at.tabs[1]

    portfolio_select = create_tab.selectbox[0].options
    assert len(portfolio_select) == len(request.config.portfolios_data)
    assert request.config.portfolios_data[0]['name'] in portfolio_select[0]

    model_select = create_tab.selectbox[1].options
    assert len(model_select) == len(request.config.models_data)
    assert request.config.models_data[0]['supplier_id'] in model_select[0]
