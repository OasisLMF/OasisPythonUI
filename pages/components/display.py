# Module to display inputs and views from api
from oasis_data_manager.errors import OasisException
import pandas as pd
import streamlit as st
import pydeck as pdk
import plotly.express as px
import geopandas

class View:
    '''
    Base class to create a view component.

    Parameters
    ----------
    data : pd.DataFrame
           Pandas DataFrame containing the data to visualise.
    '''
    def __init__(self, data):
        self.data = data

    def display(self):
        st.write(self.data)
        return None


class DataframeView(View):
    '''
    Visualise dataframe.

    Basic Usage:

    ```python
    # Initialise with df
    df_view = DataframeView(df)

    # To display
    df_view.display()
    ```

    Parameters
    ----------
    data : pd.DataFrame
           Pandas DataFrame representing the data to visualise.
    selectable : bool (default `False`)
                 If `True` then rows are selectable.
    display_cols : list[str]
                   The names of the columns to display. By default displays all the columns.
    '''
    def __init__(self, data=None, selectable=False, display_cols=None, hide_index=True):
        if data is None:
            data = pd.DataFrame(columns=display_cols)
        self.data = data
        super().__init__(self.data)
        self.selectable = selectable
        self.status_style = True
        self.hide_index = hide_index

        if display_cols is None:
            display_cols = data.columns.to_list()
        self.display_cols = display_cols

        self.column_config = {col_name: None for col_name in data.columns}
        for c in display_cols:
            if 'TIV' in c:
                self.column_config[c] = st.column_config.TextColumn(c)
            else:
                self.column_config[c] = st.column_config.TextColumn(self.format_column_heading(c))

    def display(self, max_rows=1000):
        '''
        Show the dataframe.
        '''
        if self.data.empty:
            st.dataframe(pd.DataFrame(columns=self.display_cols),
                         hide_index=self.hide_index, column_config=self.column_config,
                         column_order=self.display_cols)
            return None

        args = {
            'hide_index': self.hide_index,
            'column_config': self.column_config,
            'use_container_width': True,
            'column_order': self.display_cols
        }

        if self.selectable:
            args['selection_mode']="single-row"
            args['on_select']="rerun"

        # Add styling
        data_styled = self.data
        n_rows = data_styled.shape[0]
        # Limit if too many rows
        if n_rows > max_rows:
            data_styled = data_styled.iloc[:max_rows, :]


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

        if n_rows > max_rows:
            st.info(f"Displaying {max_rows} of {n_rows} rows.")

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
        return self

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
                 `map_type`. The `map_type` which require this parameter are:
                 `heatmap` and `choropleth`.
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
            self.generate_location_map()
        if self.map_type == "heatmap":
            assert self.weight is not None, 'Weight column not set.'
            self.generate_heatmap()
        elif self.map_type == "choropleth":
            assert self.weight is not None, 'Weight column not set'
            self.generate_choropleth()
        else:
            raise OasisException("Map type not recognised")


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

        st.pydeck_chart(deck)

    def generate_heatmap(self):
        locations = self.data

        def find_zoom_level(lon_range):
            zoom_df = pd.read_csv('./assets/zoom_levels_reduced.csv')
            masked = zoom_df[zoom_df['tile_width_longitudes'] < lon_range]
            if masked.empty:
                return 18
            return min(max(masked.iloc[0, :].name - 1, 0), 18)

        lon_range = locations[self.longitude].max() - locations[self.longitude].min()

        zoom = find_zoom_level(lon_range)

        format_weight = self.weight
        if len(format_weight) > 1:
            format_weight = format_weight[0].upper() + format_weight[1:]


        fig = px.density_map(locations,
                             lat = self.latitude,
                             lon = self.longitude,
                             z = self.weight,
                             color_continuous_scale="YlOrRd",
                             opacity=0.75,
                             zoom = zoom,
                             labels={self.weight: format_weight})
        fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        fig.update_layout(coloraxis_colorbar=dict(
            orientation='h',
            yanchor='top',
            y=0,
            lenmode='pixels',
            len=500
        ))

        st.plotly_chart(fig, use_container_width=True)

    def generate_choropleth(self):
        # Get country GeoJSON
        # Source: geojson.xyz naturalearth-3.3.0 admin_0_countries
        countries = geopandas.read_file("./assets/ne_50m_admin_0_countries_reduced.geojson")

        # Aggregate relevant data
        cols = [self.country, self.weight]
        locations = self.data[cols]
        locations = locations.groupby(self.country, as_index=False).agg('sum')

        merged = countries.merge(locations, right_on=self.country, left_on="iso_a2", how="right")
        center = {'lat': merged.geometry.centroid.y.mean(),
                  'lon': merged.geometry.centroid.x.mean()}

        if len(locations) == 1:
            range_color = [0, max(locations[self.weight])]
        else:
            offset = 0.1*(locations[self.weight].max() - locations[self.weight].min())
            range_color = [locations[self.weight].min() - offset, locations[self.weight].max() + 2*offset]

        format_weight = self.weight
        if len(format_weight) > 1:
            format_weight = format_weight[0].upper() + format_weight[1:]

        fig = px.choropleth_map(locations, geojson=countries,
                                color=self.weight,
                                locations=self.country,
                                featureidkey='properties.iso_a2',
                                color_continuous_scale="YlOrRd",
                                center=center,
                                zoom=3,
                                opacity=0.75,
                                range_color=range_color,
                                labels={self.weight: format_weight})

        fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        fig.update_layout(coloraxis_colorbar=dict(
            orientation='h',
            yanchor='top',
            y=0,
            lenmode='pixels',
            len=500
        ))

        st.plotly_chart(fig)
