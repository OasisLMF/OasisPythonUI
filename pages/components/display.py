# Module to display inputs and views from api
from oasis_data_manager.errors import OasisException
import pandas as pd
import streamlit as st
import pydeck as pdk
import plotly.express as px
import geopandas

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
            data_styled = data_styled.map(colour_status, subset=['status'])

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
    def __init__(self, data, longitude="Longitude", latitude="Latitude",
                 weight=None, map_type = "scatter", country="CountryCode"):
        '''
        Class to visualise data on a map.

        Parameters
        ----------
        data : pd.DataFrame
               Locations data.
        longitude : str
                    Longitude column name in `data`.
        latitude : str
                   Latitude column name in `data`.
        weight : str
                 Column in `data` representing the weight of each location. The
                 way the weight is visualised will be depedent on the
                 `map_type`.
        country : str
                  Country code column in `data`.
        map_type : str
                   The type of map to display. The following options are available:
                   - `scatter`
                   - `heatmap`
                   - `choropleth` - currently only supports countries.
        '''
        self.data = data
        self.longitude = longitude
        self.latitude = latitude
        self.weight = weight
        self.country = country
        self.map_type = map_type

    def display(self):

        if self.map_type == "scatter":
            deck = self.generate_location_map()
        if self.map_type == "heatmap":
            assert self.weight is not None, 'Weight column not set.'
            deck = self.generate_heatmap()
        elif self.map_type == "choropleth":
            assert self.weight is not None, 'Weight column not set'
            deck = self.generate_choropleth()
            return None
        else:
            OasisException("Map type not recognised")

        st.pydeck_chart(deck, use_container_width=True)
        return None

    def generate_location_map(self):
        locations = self.data

        layer = pdk.Layer(
            'ScatterplotLayer',
            locations,
            get_position=[self.longitude, self.latitude],
            get_line_color = [0, 0, 0],
            get_fill_color = [255, 140, 0],
            radius_min_pixels = 1,
            radius_max_pixels = 50,
            radius_scale = 2,
            pickable=True,
            stroked=True,
            get_line_width=0.5,
        )

        viewstate = pdk.data_utils.compute_view(locations[[self.longitude, self.latitude]])

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

    def generate_heatmap(self):
        locations = self.data

        viewstate = pdk.data_utils.compute_view(locations[[self.longitude, self.latitude]])

        layer = pdk.Layer(
                'HeatmapLayer',
                data = locations,
                opacity = 0.9,
                get_position = [self.longitude, self.latitude],
                aggregation = pdk.types.String("SUM"),
                threshold = 1,
                pickable = True,
                get_weight = self.weight
        )

        # Prevent over zooming
        if viewstate.zoom > 18:
            viewstate.zoom = 18

        deck = pdk.Deck(layers=[layer], initial_view_state=viewstate,
                        map_style='light')

        return deck

    def generate_choropleth(self):
        # Get country GeoJSON
        # Source: geojson.xyz naturalearth-3.3.0 admin_0_countries
        countries = geopandas.read_file("./assets/ne_50m_admin_0_countries_reduced.geojson")
        countries = countries.set_index('iso_a2')

        # Aggregate relevant data
        cols = [self.country, self.weight]
        locations = self.data[cols]
        locations = locations.groupby(self.country, as_index=False).agg('sum')


        # Assign colors
        colour_col = locations[self.weight]
        colour_col = (colour_col - colour_col.min()) / (colour_col.max() - colour_col.min())
        colour_col = colour_col.fillna(0)
        colour_col = px.colors.sample_colorscale("inferno", colour_col)
        colour_col = [px.colors.unlabel_rgb(c) for c in colour_col]

        locations["country_colour"] = colour_col
        locations = countries.merge(locations, left_on="iso_a2", right_on=self.country)

        long_init = float(locations.geometry.centroid.x.mean())
        lat_init = float(locations.geometry.centroid.y.mean())

        layer = pdk.Layer(
                    "GeoJsonLayer",
                    data = locations,
                    opacity = 0.4,
                    filled = True,
                    wireframe = True,
                    get_line_color = [255, 255, 255],
                    get_fill_color = "country_colour",
                    get_line_width = 500,
                    stroked = True,
                    pickable=True
        )

        deck = pdk.Deck(layers=[layer],
                        initial_view_state = {
                            'longitude': long_init,
                            'latitude':  lat_init,
                            'zoom' : 2
                        },
                        map_style="light",
                        tooltip = {
                            'html': f'''
                                    <b>Country:</b> {{name}}<br />
                                    <b>{self.weight}:</b> {{{self.weight}}}
                                    '''
                        }
                        )


        st.pydeck_chart(deck)
