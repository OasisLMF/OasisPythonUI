"""
File containig some common methods for `pages/`.
"""
import streamlit as st
from urllib.parse import urlparse
from pathlib import PurePosixPath

PERSPECTIVES_MAP = {
        'gul': 'Group-up loss',
        'il': 'Insured loss',
        'ri': 'Reinsured loss'
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
    """Get the current page path from streamlit context.
    """
    return PurePosixPath(urlparse(st.context.url).path).parts[-1]
