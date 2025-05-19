from oasis_data_manager.errors import OasisException
import pandas as pd

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
        else:
            data['id'].append(id)
            data[col_name].append(file_df.shape[0])
    return pd.DataFrame(data)

def enrich_portfolios(portfolios, client_interface, disable=[]):
    '''
    Add summary information columns to portfolios dataframe. Currently supports the following column options:
        - `loc` : The number of locations in the location file.
        - `acc` : The number of accounts in the accounts file

    Args:
        portfolios : DataFrame containing output from portfolios endpoint.
        client_interface : ClientInterface instance.
        disable : List of column options to ignore.

    Returns:
        The new enriched portfolio.
    '''
    enriched = None
    if 'loc' not in disable:
        filtered_portfolios = portfolios[portfolios['location_file.stored'].notna()]['id']
        _n_loc_df = number_rows(filtered_portfolios, client_interface,
                                filename='location_file',
                                col_name='number_locations')
        enriched = _n_loc_df.set_index('id')
    if 'acc' not in disable:
        filtered_portfolios = portfolios[portfolios['accounts_file.stored'].notna()]['id']
        _n_acc_df = number_rows(filtered_portfolios, client_interface,
                                    filename='accounts_file',
                                    col_name='number_accounts')
        _n_acc_df = _n_acc_df.set_index('id')
        if enriched is None:
            enriched = _n_acc_df
        else:
            enriched = enriched.join(_n_acc_df)

    if enriched is not None:
        portfolios =  portfolios.set_index('id').join(enriched).reset_index(names='id')

    return portfolios

def enrich_analyses_with_portfolios(analyses, portfolios):
    portfolios = portfolios[['id', 'name']].rename(columns={'name': 'portfolio_name'})
    analyses = analyses.set_index('portfolio').join(portfolios.set_index('id')).reset_index(names='portfolio')

    return analyses

def enrich_analyses_with_models(analyses, models):
    models = models[['id', 'model_id', 'supplier_id']].rename(columns={'supplier_id': 'model_supplier'})
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
