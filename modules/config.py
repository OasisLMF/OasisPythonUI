import json
import os
import streamlit as st
import logging

logger = logging.getLogger(__name__)
OASIS_UI_CONFIG = "ui-config.json"

class UIConfig():
    """Class to hold config information for the UI. Loads the infomation from
    OASIS_UI_CONFIG environment variabel (defaults to `ui-config.json`).

    Attributes:
        pages: List of strings for each subdomains displayed.
        post_login_page: Subdomain to redirect to after login.
        model_map: dict where the key is the model name and the value is a list
        of exposure sets the model should correspond to.
    """
    def __init__(self):
        config_path = os.getenv("OASIS_UI_CONFIG", OASIS_UI_CONFIG)

        if os.path.isfile(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
        else:
            logger.warning(f"OASIS_UI_CONFIG: {config_path} not found.")
            config = {}

        self.pages = config.get('pages', [])
        self.post_login_page = config.get('post_login_page')
        self.model_map = config.get('model_map', {})


def retrieve_ui_config():
    '''Retrieve ui config.

    First checks `session_state` and if not present loads from file.
    '''
    if 'ui-config' in st.session_state:
        logger.info("Loading ui-config from session_state.")
        return st.session_state['ui-config']

    logger.info("Loading ui-config from file.")
    ui_config = UIConfig()
    st.session_state['ui-config'] = ui_config
    return ui_config
