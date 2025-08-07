from modules.config import retrieve_ui_config
from modules.logging import get_session_logger
import streamlit as st

from pages.components.common import get_page_path

logger = get_session_logger()

def generate_footer(ui_config=None):
    if ui_config is None:
        ui_config = retrieve_ui_config()

    if ui_config.footer is None:
        return

    assert "path" in ui_config.footer, "No footer path in config."

    try:
        with open(ui_config.footer.get("path") , "r") as f:
            footer_txt = f.read()

        page_path = get_page_path()
        if "pages" in ui_config.footer and page_path in ui_config.footer["pages"]:
            logger.info(f"Footer applied to {page_path}.")
            st.write('---')
            st.caption(footer_txt)

    except FileNotFoundError as _:
        logger.error(f"Footer file not found as path {ui_config.footer['path']}")
