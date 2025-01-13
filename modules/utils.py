import streamlit as st
import pandas as pd

def selected_to_row(selected, df):
    selected = selected["selection"]["rows"]

    if len(selected) > 0:
        return df.iloc[selected[0]]
    return None

def convert_datetime_cols(df, cols):
    for c in cols:
        df[c] = pd.to_datetime(df[c])
    return df

def generate_column_config(col_names, display_cols, date_time_cols=None):
    config = {name: None for name in col_names}
    for c in display_cols:
        config[c] = c.replace('_', ' ').title()

    if date_time_cols is None:
        return config

    for c in date_time_cols:
        config[c] = st.column_config.DatetimeColumn(config[c],
                                                    format="DD/MM/YY HH:mm:ss")

    return config
