"""Loading and shaping platform records for the standard UI pages.

List endpoints are always fetched fresh. Larger payloads (exposure files,
analysis inputs/outputs) are cached per session, keyed on the record's
`modified` timestamp, so they refresh after any change but are not shared
between users.
"""
import logging
import re

import pandas as pd
import streamlit as st
from requests.exceptions import HTTPError

from modules.client import PortfoliosEndpointInterface
from pages.components.common import format_status

logger = logging.getLogger(__name__)

_CACHE_KEY = '_session_data_cache'
_CACHE_MAX = 20


def session_cached(key, loader):
    """Return `loader()` cached in this session under `key`."""
    cache = st.session_state.setdefault(_CACHE_KEY, {})
    if key not in cache:
        if len(cache) >= _CACHE_MAX:
            cache.pop(next(iter(cache)))
        cache[key] = loader()
    return cache[key]


def _to_datetime(df, cols=('created', 'modified')):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors='coerce')
    return df


##########################################################################################
# Portfolios
##########################################################################################

FILE_TYPES = PortfoliosEndpointInterface.FILE_TYPES


# Filename patterns used to guess which OED file an upload is, checked in order
_FILE_PATTERNS = [
    ('reinsurance_info_file', r'(ri|reins).*info|info'),
    ('reinsurance_scope_file', r'(ri|reins).*scope|scope'),
    ('location_file', r'loc'),
    ('accounts_file', r'acc'),
]


def guess_file_type(filename):
    """Guess the portfolio file type from an uploaded file's name (or None)."""
    name = filename.lower()
    for file_type, pattern in _FILE_PATTERNS:
        if re.search(pattern, name):
            return file_type
    return None


def portfolios_df(portfolios, analyses=None):
    """Portfolio records as a DataFrame with file-presence and analysis-count columns."""
    rows = []
    for p in portfolios:
        row = {'id': p['id'], 'name': p['name'],
               'created': p.get('created'), 'modified': p.get('modified')}
        for f in FILE_TYPES:
            row[f] = bool((p.get(f) or {}).get('stored'))
        rows.append(row)
    df = pd.DataFrame(rows, columns=['id', 'name', 'created', 'modified', *FILE_TYPES])
    if analyses is not None:
        counts = pd.Series([a['portfolio'] for a in analyses], dtype='Int64').value_counts()
        df['n_analyses'] = df['id'].map(counts).fillna(0).astype(int)
    return _to_datetime(df)


def portfolio_file_df(ci, portfolio, file_type):
    """Dataframe of one of a portfolio's OED files (cached until it changes)."""
    if not (portfolio.get(file_type) or {}).get('stored'):
        return None
    key = ('portfolio_file', portfolio['id'], file_type, portfolio.get('modified'),
           portfolio[file_type]['stored'])
    return session_cached(key, lambda: ci.portfolios.get_file(portfolio['id'], file_type, df=True))


##########################################################################################
# Models
##########################################################################################

def model_settings(ci, model_id):
    """Model settings dict ({} if the model has none registered)."""
    try:
        return ci.models.settings.get(model_id) or {}
    except HTTPError as e:
        logger.warning(f'No settings for model {model_id}: {e}')
        return {}


def model_label(model, settings=None):
    name = (settings or {}).get('name') or model.get('model_id')
    return f"{name} ({model.get('supplier_id')}, {model.get('version_id')})"


def models_df(ci, models, analyses=None):
    rows = []
    for m in models:
        settings = session_cached(('model_settings', m['id'], m.get('modified')),
                                  lambda: model_settings(ci, m['id']))
        rows.append({
            'id': m['id'],
            'name': settings.get('name') or m['model_id'],
            'supplier_id': m.get('supplier_id'),
            'model_id': m.get('model_id'),
            'version_id': m.get('version_id'),
            'run_mode': m.get('run_mode'),
            'created': m.get('created'),
            'modified': m.get('modified'),
        })
    df = pd.DataFrame(rows, columns=['id', 'name', 'supplier_id', 'model_id', 'version_id',
                                     'run_mode', 'created', 'modified'])
    if analyses is not None:
        counts = pd.Series([a['model'] for a in analyses], dtype='Int64').value_counts()
        df['n_analyses'] = df['id'].map(counts).fillna(0).astype(int)
    return _to_datetime(df)


def cached_model_settings(ci, model):
    return session_cached(('model_settings', model['id'], model.get('modified')),
                          lambda: model_settings(ci, model['id']))


##########################################################################################
# Analyses
##########################################################################################

def analyses_df(analyses, portfolios, models_frame):
    """Analysis records enriched with portfolio and model names."""
    portfolio_names = {p['id']: p['name'] for p in portfolios}
    model_names = dict(zip(models_frame['id'], models_frame['name'])) if not models_frame.empty else {}
    rows = []
    for a in analyses:
        rows.append({
            'id': a['id'],
            'name': a['name'],
            'status': a.get('status'),
            'status_label': format_status(a.get('status')),
            'portfolio': a.get('portfolio'),
            'portfolio_name': portfolio_names.get(a.get('portfolio'), f"#{a.get('portfolio')}"),
            'model': a.get('model'),
            'model_name': model_names.get(a.get('model'), f"#{a.get('model')}"),
            'created': a.get('created'),
            'modified': a.get('modified'),
        })
    df = pd.DataFrame(rows, columns=['id', 'name', 'status', 'status_label', 'portfolio',
                                     'portfolio_name', 'model', 'model_name', 'created', 'modified'])
    return _to_datetime(df).sort_values('id', ascending=False)


def analysis_settings(ci, analysis):
    if not analysis.get('settings'):
        return None
    try:
        return ci.analyses.settings.get(analysis['id'])
    except HTTPError as e:
        logger.warning(f"No settings for analysis {analysis['id']}: {e}")
        return None


def analysis_files(ci, analysis, file_type):
    """Input or output files for an analysis as `{filename: DataFrame}`."""
    key = (file_type, analysis['id'], analysis.get('modified'))
    return session_cached(key, lambda: ci.analyses.get_file(analysis['id'], file_type, df=True) or {})
