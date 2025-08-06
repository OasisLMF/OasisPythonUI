import streamlit as st
import logging


def get_session_logger(log_level=logging.INFO):
    if 'logger' not in st.session_state:
        logger = logging.getLogger(__name__)
        logger.addHandler(logging.StreamHandler())
        logger.setLevel(log_level)
        st.session_state['logger'] = logger
    else:
        logger = st.session_state.get('logger')

    return logger
