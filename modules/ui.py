"""Shared page scaffolding and feedback helpers for the standard UI pages."""
import json
import logging

import streamlit as st
from requests.exceptions import HTTPError

from modules.authorisation import handle_login, validate_page
from modules.config import retrieve_ui_config
from modules.nav import SidebarNav

logger = logging.getLogger(__name__)

_FLASH_KEY = '_flash_messages'


def page_setup(label, title=None):
    """Configure, authorise and add navigation to a page.

    Args:
        label: page label as configured in `ui-config.json`.
        title: page heading (defaults to `label`).

    Returns:
        ClientInterface for the logged-in session.
    """
    ui_config = retrieve_ui_config()
    st.set_page_config(page_title=f'{label} · Oasis', layout='wide')
    validate_page(label)
    handle_login(ui_config.skip_login)
    SidebarNav()
    show_flash()
    st.title(title or label)
    return st.session_state['client_interface']


def flash(message, icon='✅'):
    """Queue a toast to show after the next rerun (st.toast alone is lost on rerun)."""
    st.session_state.setdefault(_FLASH_KEY, []).append((message, icon))


def show_flash():
    for message, icon in st.session_state.pop(_FLASH_KEY, []):
        st.toast(message, icon=icon)


def api_error_message(error):
    """Human readable message for an API error, including the server's reason."""
    if isinstance(error, HTTPError) and error.response is not None:
        try:
            detail = error.response.json()
            if isinstance(detail, dict):
                detail = '; '.join(f'{k}: {v}' for k, v in detail.items())
            elif isinstance(detail, list):
                detail = '; '.join(str(d) for d in detail)
        except (ValueError, json.JSONDecodeError):
            detail = error.response.text[:500]
        return f'{error.response.status_code} {error.response.reason}: {detail}'
    return str(error)


def show_api_error(action, error):
    logger.error(f'{action} failed: {error}')
    st.error(f'{action} failed. {api_error_message(error)}')
