from oasis_data_manager.errors import OasisException
import pandas as pd
from requests.models import HTTPError
import streamlit as st

from modules.client import ClientInterface
from modules.logging import get_session_logger

logger = get_session_logger()

def number_rows(portfolio_ids, client_interface, filename='location_file', col_name='number_rows'):
    data = {'id': [], col_name: []}
    for id in portfolio_ids:
        file_func = getattr(client_interface.portfolios, f'get_{filename}', None)
        if file_func is None:
            raise OasisException('Portfolio file endpoint not found.')

        file_df = file_func(id, df=True)
        if file_df is None:
            data['id'].append(id)
            data[col_name].append(None)

        data['id'].append(id)
        data[col_name].append(file_df.shape[0])
    return pd.DataFrame(data)


def number_locations(portfolio_ids, client_interface):
    return number_rows(portfolio_ids, client_interface, filename='location_file', col_name='number_locations')

def number_accounts(portfolio_ids, client_interface):
    return number_rows(portfolio_ids, client_interface, filename='accounts_file', col_name='number_accounts')

def portfolio_files(portfolios):
    enriched = portfolios['id'].to_frame()
    st.write(portfolios)
    enriched['contains_location'] = portfolios['location_file.stored'].notna()
    enriched['contains_accounts'] = portfolios['accounts_file.stored'].notna()
    enriched['contains_ri_info'] = portfolios['reinsurance_info_file.stored'].notna()
    enriched['contains_ri_scope'] = portfolios['reinsurance_scope_file.stored'].notna()
    return enriched


def enrich_portfolios(portfolios, client_interface,
                      disable=[]):
    """Enrich portfolios dataframe with additional columns. Each new column is given a key which can be disabled with the `disable` kwarg. The columns added and keys are listed below:

    'loc': 'number_locations'
    'acc': 'number_accounts'
    'files': ['contains_location', 'contains_accounts', 'contains_ri_info', 'contains_ri_scope']
    """
    enriched = []
    if 'loc' not in disable:
        _n_loc_df = number_locations(portfolios[portfolios['location_file.stored'].notna()]['id'], client_interface)
        enriched.append(_n_loc_df.set_index('id'))
    if 'acc' not in disable:
        _n_acc_df = number_accounts(portfolios[portfolios['accounts_file.stored'].notna()]['id'], client_interface)
        _n_acc_df = _n_acc_df.set_index('id')
        enriched.append(_n_acc_df)

    if 'files' not in disable:
        enriched.append(portfolio_files(portfolios).set_index('id'))

    if enriched:
        portfolios = portfolios.set_index('id').join(enriched).reset_index(names='id')

    return portfolios


def enrich_analyses_with_portfolios(analyses, portfolios):
    portfolios = portfolios[['id', 'name']].rename(columns={'name': 'portfolio_name'})
    analyses = analyses.set_index('portfolio').join(portfolios.set_index('id')).reset_index(names='portfolio')

    return analyses

def enrich_analyses_with_models(analyses, models):
    cols = ['id', 'model_id', 'supplier_id']
    if 'model_name' in models:
        cols += ['model_name']
    models = models[cols].rename(columns={'supplier_id': 'model_supplier'})
    analyses = analyses.set_index('model').join(models.set_index('id')).reset_index(names='model')

    return analyses

def enrich_analyses(analyses, portfolios=None, models=None):
    # add portfolio names
    if portfolios is not None:
        analyses = enrich_analyses_with_portfolios(analyses, portfolios)

    # add model names
    if models is not None:
        analyses = enrich_analyses_with_models(analyses, models)

    return analyses


@st.cache_data(ttl="1d", hash_funcs={ClientInterface: lambda ci: ci.client.api.tkn_access})
def add_model_names_to_models_cached(models: pd.DataFrame,
                                     ci: ClientInterface,
                                     col_name='model_name'):
    return add_model_names_to_models(models, ci, col_name)


def add_model_names_to_models(models, ci, col_name='model_name'):
    '''Add the model names to models. Note the model `id` should be the index of the models.

    Args:
        models (DataFrame): dataframe containing models endpoint output
        ci (ClientInterface): intialised client interface
        col_name (str) : column name for model names
    '''
    models[col_name] = ''
    for model_id, _ in models.iterrows():
        try:
            models.at[model_id, col_name] = ci.models.settings.get(model_id).get('name', None)
        except HTTPError as _:
            models.at[model_id, col_name] = None
            logger.warning(f'No settings for model_id: {model_id}')

    models[col_name] = models[col_name].fillna(models['model_id'])

    return models

