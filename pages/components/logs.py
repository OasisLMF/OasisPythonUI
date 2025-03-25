import streamlit as st

def display_traceback_file(tb_text, trace_type):
    fname = f'{trace_type}_traceback_file'
    n_lines = 20
    display_lines = tb_text.splitlines()
    if len(display_lines) > n_lines:
        display_lines = display_lines[-n_lines:]

    display_lines = '\n'.join(display_lines)
    st.write(f'End of `{fname}`:')
    st.code(display_lines)
    fname += '.txt'
    st.download_button(label=f'Download', data=tb_text, file_name=fname,
                       key=f'{fname}_download_button')
