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

        data['id'].append(id)
        data[col_name].append(file_df.shape[0])
    return pd.DataFrame(data)


def number_locations(portfolio_ids, client_interface):
    return number_rows(portfolio_ids, client_interface, filename='location_file', col_name='number_locations')

def number_accounts(portfolio_ids, client_interface):
    return number_rows(portfolio_ids, client_interface, filename='accounts_file', col_name='number_accounts')


def enrich_portfolios(portfolios, client_interface):
    num_locations = number_locations(portfolios[portfolios['location_file.stored'].notna()]['id'], client_interface)
    num_accounts = number_accounts(portfolios[portfolios['accounts_file.stored'].notna()]['id'], client_interface)

    enriched_columns = num_locations.set_index('id').join(num_accounts.set_index('id'))
    portfolios =  portfolios.set_index('id').join(enriched_columns).reset_index()

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
