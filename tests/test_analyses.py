import tests.mocks as m
from tests.conftest import page_app

from pages.components.common import NEW_ANALYSIS_DEFAULTS, SELECTED_ANALYSIS

PAGE = 'pages/analyses.py'


def test_empty_analyses_page():
    at = page_app(PAGE, m.MockApiClient())

    assert not at.exception
    assert at.title[0].value == 'Analyses'
    assert at.button[0].label == 'New analysis'
    assert 'No analyses yet. Create one to get started.' in [i.value for i in at.info]


def test_analyses_table(mock_app_test, request):
    config = request.config
    at = mock_app_test
    assert not at.exception

    table = at.dataframe[0].value
    assert len(table) == 1
    row = table.iloc[0]
    assert row['id'] == config.analyses_ID
    assert row['name'] == config.analyses_data[0]['name']
    assert row['status_label'] == '🆕 New'
    assert row['portfolio_name'] == config.portfolios_data[0]['name']
    assert row['model_name'] == config.models_data[0]['model_id']


def test_selected_analysis_shows_detail(mock_api_client, request):
    at = page_app(PAGE, mock_api_client, {SELECTED_ANALYSIS: request.config.analyses_ID})

    assert not at.exception
    assert at.subheader[0].value == request.config.analyses_data[0]['name']
    assert [t.label for t in at.tabs] == ['Results', 'Settings', 'Inputs', 'Logs']
    # No settings yet, so it can't be run
    run = [b for b in at.button if b.label == 'Run'][0]
    assert run.disabled


def test_new_analysis_view_from_portfolio(mock_api_client, request):
    config = request.config
    at = page_app(PAGE, mock_api_client, {NEW_ANALYSIS_DEFAULTS: {'portfolio': config.portfolio_ID}})

    assert not at.exception
    assert at.subheader[0].value == 'New analysis'
    assert at.selectbox(key='new_analysis_portfolio').value == config.portfolio_ID
    # Only one model, so it is preselected
    assert at.selectbox(key='new_analysis_model').value == config.model_ID
    assert [t.label for t in at.tabs] == ['General', 'Model options', 'Outputs', 'Review']


def test_create_analysis(mock_api_client, request):
    config = request.config
    at = page_app(PAGE, mock_api_client, {NEW_ANALYSIS_DEFAULTS: {'portfolio': config.portfolio_ID}})

    at.text_input(key='new_analysis_name').input('my analysis').run()
    [b for b in at.button if b.label == 'Create only'][0].click().run()

    assert not at.exception
    created = [a for a in mock_api_client.analyses.json_data if a['name'] == 'my analysis']
    assert len(created) == 1
    assert created[0]['status'] == 'NEW'
    settings = mock_api_client.analyses.settings.data[created[0]['id']]
    assert settings['model_name_id'] == config.models_data[0]['model_id']
    assert settings['gul_output'] is True
    # Back on the list with the new analysis selected
    assert at.session_state[SELECTED_ANALYSIS] == created[0]['id']
    assert at.session_state['analyses_view'] is None


def test_create_and_run_analysis(mock_api_client, request):
    config = request.config
    at = page_app(PAGE, mock_api_client, {NEW_ANALYSIS_DEFAULTS: {'portfolio': config.portfolio_ID}})

    [b for b in at.button if b.label == 'Create and run'][0].click().run()

    assert not at.exception
    created = mock_api_client.analyses.json_data[-1]
    assert created['status'] == 'INPUTS_GENERATION_QUEUED'
    # Name defaults to "<portfolio> – <model>"
    assert created['name'] == f"{config.portfolios_data[0]['name']} – {config.models_data[0]['model_id']}"


def _template_options(client, request):
    at = page_app(PAGE, client, {NEW_ANALYSIS_DEFAULTS: {'portfolio': request.config.portfolio_ID}})
    assert not at.exception
    return at.selectbox(key=f'new_{request.config.model_ID}_template').options


def test_defaults_files_only_without_platform_templates(mock_api_client, request, monkeypatch):
    monkeypatch.setattr('modules.settings.get_analyses_settings',
                        lambda **kwargs: ['defaults/1_model_supplier-analysis_settings.json'])

    # No platform templates: the bundled defaults file is offered
    assert 'Default file: 1_model_supplier-analysis_settings.json' in _template_options(mock_api_client, request)

    # With a platform template, only the template is offered
    mock_api_client.models.setting_templates.data[request.config.model_ID] = [{'id': 3, 'name': 'Standard'}]
    options = _template_options(mock_api_client, request)
    assert options[0] == 'Template: Standard'
    assert not any(o.startswith('Default file') for o in options)
