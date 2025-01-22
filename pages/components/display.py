# Module to display inputs and views from api
import pandas as pd
import streamlit as st
import pydeck as pdk

class View:
    def __init__(self, data):
        self.data = data

    def display(self):
        st.write(self.data)
        return None


class DataframeView(View):
    def __init__(self, data=None, selectable=False, display_cols=None):
        if data is None:
            data = pd.DataFrame(columns=display_cols)
        self.data = data
        super().__init__(self.data)
        self.selectable = selectable
        self.status_style = True

        if display_cols is None:
            display_cols = data.columns.to_list()
        self.display_cols = display_cols

        self.column_config = {col_name: None for col_name in data.columns}
        for c in display_cols:
            if 'TIV' in c:
                self.column_config[c] = st.column_config.TextColumn(c)
            else:
                self.column_config[c] = st.column_config.TextColumn(self.format_column_heading(c))

    def display(self):
        if self.data.empty:
            st.dataframe(pd.DataFrame(columns=self.display_cols),
                         hide_index=True, column_config=self.column_config,
                         column_order=self.display_cols)
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


        # Add styling
        data_styled = self.data

        def format_status(status):
            return status.replace('_', ' ').title()

        def colour_status(status):
            colour = 'black'
            if status == 'READY':
                colour = 'green'
            elif status == 'RUN_STARTED':
                colour = 'goldenrod'
            elif status == 'RUN_COMPLETED':
                colour = 'black'
            elif status in ['RUN_CANCELLED', 'RUN_ERROR']:
                colour = 'darkred'
            return f'color: {colour}'

        if self.status_style and 'status' in self.data.columns:
            data_styled = data_styled.style.format(format_status, subset=['status'])
            data_styled = data_styled.applymap(colour_status, subset=['status'])

        ret = st.dataframe(data_styled, **args)

        if self.selectable:
            return self.selected_to_row(ret)

        return None

    def convert_datetime_cols(self, datetime_cols):
        for c in datetime_cols:
            if c not in self.display_cols or c not in self.data.columns:
                continue
            self.data[c] = pd.to_datetime(self.data[c])
            self.column_config[c] = st.column_config.DatetimeColumn(self.format_column_heading(c),
                                                                    format="hh:mm a, D MMM YY")
        return self.data

    @staticmethod
    def format_column_heading(heading):
        return heading.replace('_', ' ').title().replace('Id', 'ID')

    def selected_to_row(self, selected):
        selected = selected["selection"]["rows"]

        if len(selected) > 0:
            return self.data.iloc[selected[0]]
        return None


class MapView(View):
    def __init__(self, data, longitude="Longitude", latitude="Latitude"):
        self.data = data
        self.longitude_key = longitude
        self.latitude_key = latitude

    def display(self):
        deck = self.generate_location_map()
        st.pydeck_chart(deck, use_container_width=True)
        return None

    def generate_location_map(self):
        locations = self.data

        layer = pdk.Layer(
            'ScatterplotLayer',
            locations,
            get_position=[self.longitude_key, self.latitude_key],
            get_line_color = [0, 0, 0],
            get_fill_color = [255, 140, 0],
            radius_min_pixels = 1,
            radius_max_pixels = 50,
            radius_scale = 2,
            pickable=True,
            stroked=True,
            get_line_width=0.5,
        )

        viewstate = pdk.data_utils.compute_view(locations[[self.longitude_key, self.latitude_key]])

        # Prevent over zooming
        if viewstate.zoom > 18:
            viewstate.zoom = 18


        tooltip = {'text': ''}
        if 'LocPerilsCovered' in locations.columns:
            tooltip['text'] += "Peril: {LocPerilsCovered}"
        if 'BuildingTIV' in locations.columns:
            tooltip['text'] += "\nBuilding TIV: {BuildingTIV}"
        deck = pdk.Deck(layers=[layer], initial_view_state=viewstate,
                        tooltip=tooltip,
                        map_style='light')
        return deck
