# Module to display inputs and views from api
import pandas as pd
import streamlit as st


class DataframeView:
    def __init__(self, df=None, selectable=False, display_cols=None):
        if df is None:
            df = pd.DataFrame(columns=display_cols)
        self.df = df
        self.selectable = selectable

        if display_cols is None:
            display_cols = df.columns
        self.display_cols = display_cols

        self.column_config = {col_name: None for col_name in df.columns}
        for c in display_cols:
            self.column_config[c] = st.column_config.TextColumn(self.format_column_heading(c))
            if c == 'id':
                self.column_config[c] = st.column_config.TextColumn("ID")

    def display(self):
        if self.df.empty:
            st.dataframe(self.df, hide_index=True, column_order=self.display_cols)
            return None

        args = {
            'hide_index': True,
            'column_config': self.column_config,
            'use_container_width': True,
            'column_order': self.display_cols
        }

        if self.selectable:
            args['selection_mode']="single-row"
            args['on_select']="rerun"

        ret = st.dataframe(self.df, **args)

        if self.selectable:
            return self.selected_to_row(ret)

        return None

    def convert_datetime_cols(self, datetime_cols):
        for c in datetime_cols:
            self.df[c] = pd.to_datetime(self.df[c])
            self.column_config[c] = st.column_config.DatetimeColumn(self.format_column_heading(c),
                                                                    format="hh:mm a, D MMM YY")
        return self.df

    @staticmethod
    def format_column_heading(heading):
        return heading.replace('_', ' ').title()

    def selected_to_row(self, selected):
        selected = selected["selection"]["rows"]

        if len(selected) > 0:
            return self.df.iloc[selected[0]]
        return None
