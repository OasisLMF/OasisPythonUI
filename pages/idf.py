import streamlit as st
from modules.nav import SidebarNav
from modules.client import get_portfolios, get_analyses, get_models
from pages.components.display import DataframeView

st.set_page_config(
    page_title = "IDF Demo",
    layout = "centered"
)

SidebarNav()

"# OasisLMF UI - IDF Demo"

if "client" in st.session_state:
    client = st.session_state.client
else:
    st.switch_page("app.py")

'## Portfolios'

datetime_cols = ['created', 'modified']
display_cols = [ 'id', 'name', 'created', 'modified', ]

portfolios = get_portfolios(client)
portfolio_view = DataframeView(portfolios, display_cols=display_cols)
portfolio_view.convert_datetime_cols(datetime_cols)
portfolio_view.display()

'## Models'
models = get_models(client)
display_cols = ['id', 'supplier_id', 'model_id', 'version_id', 'created', 'modified']
datetime_cols = ['created', 'modified']

model_view = DataframeView(models, selectable=True, display_cols=display_cols)
model_view.convert_datetime_cols(datetime_cols)
selected = model_view.display()

'## Analyses'
analyses = get_analyses(client)
display_cols = [ 'id', 'name', 'portfolio', 'model', 'created', 'modified',
                'status' ]
datetime_cols = ['created', 'modified']

analyses_view = DataframeView(analyses, display_cols=display_cols)
analyses_view.convert_datetime_cols(datetime_cols)
analyses_view.display()
