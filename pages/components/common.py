"""File containig some common methods for `pages/`."""
from modules.status import IN_PROGRESS_STATUSES, is_active  # noqa: F401 - re-exported
import streamlit as st
from urllib.parse import urlparse
from pathlib import PurePosixPath

PERSPECTIVES_MAP = {
    'gul': 'Ground Up Loss',
    'il': 'Insured Loss',
    'ri': 'Reinsured Loss'
}

STATUS_COLORS = {
    'NEW': 'green',
    'READY': 'green',
    'RUN_STARTED': 'goldenrod',
    'RUN_QUEUED': 'goldenrod',
    'RUN_CANCELLED': 'darkred',
    'RUN_ERROR': 'darkred',
    'INPUTS_GENERATION_QUEUED': 'goldenrod',
    'INPUTS_GENERATION_STARTED': 'goldenrod',
    'INPUTS_GENERATION_CANCELLED': 'darkred',
    'INPUTS_GENERATION_ERROR': 'darkred'
}


def get_page_path():
    """Get the current page path from streamlit context."""
    return PurePosixPath(urlparse(st.context.url).path).parts[-1]


##########################################################################################
# Status helpers
##########################################################################################

STATUS_ICONS = {
    'NEW': '🆕',
    'INPUTS_GENERATION_QUEUED': '⏳',
    'INPUTS_GENERATION_STARTED': '⏳',
    'INPUTS_GENERATION_CANCELLED': '⛔',
    'INPUTS_GENERATION_ERROR': '❌',
    'READY': '🟢',
    'RUN_QUEUED': '⏳',
    'RUN_STARTED': '⏳',
    'RUN_COMPLETED': '✅',
    'RUN_CANCELLED': '⛔',
    'RUN_ERROR': '❌',
}

ERROR_STATUSES = ['INPUTS_GENERATION_ERROR', 'RUN_ERROR']


def format_status(status):
    """e.g. `RUN_COMPLETED` -> `✅ Run completed`."""
    if not isinstance(status, str):
        return ''
    label = status.replace('_', ' ').capitalize()
    return f"{STATUS_ICONS.get(status, '')} {label}".strip()


def status_label(analysis):
    """Status label for an analysis, showing the READY gap of a generate-and-run as starting."""
    if analysis.get('status') == 'READY' and is_active(analysis):
        return '⏳ Inputs ready, starting run'
    return format_status(analysis.get('status'))


def analysis_progress(analysis):
    """Progress of a running analysis as `(fraction or None, description)`.

    Uses the events completed during the loss calculation when the worker
    reports them (needs `OASIS_ANALYSIS_STATUS_URL` set on the worker),
    otherwise the sub-task counts.
    """
    events_total = analysis.get('num_events_total') or 0
    events_done = analysis.get('num_events_complete') or 0
    if analysis.get('status') == 'RUN_STARTED' and events_total:
        return min(events_done / events_total, 1.0), f'{events_done:,} of {events_total:,} events'

    counts = analysis.get('status_count') or {}
    total = counts.get('TOTAL') or 0
    if total:
        done = counts.get('COMPLETED', 0)
        return done / total, f'{done} of {total} tasks'
    return None, ''


def current_task(sub_tasks):
    """Name of the sub-task(s) being worked on, e.g. "Generate losses chunk 0".

    Falls back to the next queued task when nothing has started yet.
    """
    started = [t.get('name') for t in sub_tasks if t.get('status') == 'STARTED' and t.get('name')]
    if started:
        return ', '.join(dict.fromkeys(started))
    queued = [t.get('name') for t in sub_tasks if t.get('status') in ('QUEUED', 'PENDING') and t.get('name')]
    return f'Waiting for: {queued[0]}' if queued else ''


##########################################################################################
# Tables and selection
##########################################################################################

def selectable_table(df, columns, state_key, column_config=None, key=None, height='auto'):
    """Show `df` as a single-row selectable table and remember the selected `id`.

    The selection is stored in `st.session_state[state_key]` so that other
    pages can preselect a record (set the key, then `st.switch_page`).

    Returns:
        The selected record id, or None.
    """
    key = key or f'{state_key}_table'
    ids = df['id'].tolist() if not df.empty else []

    def on_select():
        rows = st.session_state[key].selection.rows
        st.session_state[state_key] = ids[rows[0]] if rows else None

    st.dataframe(df, key=key, on_select=on_select, selection_mode='single-row',
                 hide_index=True, column_order=columns, column_config=column_config or {},
                 width='stretch', height=height)

    selected = st.session_state.get(state_key)
    return selected if selected in ids else None


def open_record(page, state_key, record_id):
    """Navigate to `page` with `record_id` preselected."""
    st.session_state[state_key] = record_id
    st.switch_page(page)


SELECTED_PORTFOLIO = 'selected_portfolio_id'
SELECTED_MODEL = 'selected_model_id'
SELECTED_ANALYSIS = 'selected_analysis_id'
NEW_ANALYSIS_DEFAULTS = 'new_analysis_defaults'

PORTFOLIOS_PAGE = 'pages/portfolios.py'
MODELS_PAGE = 'pages/models.py'
ANALYSES_PAGE = 'pages/analyses.py'
