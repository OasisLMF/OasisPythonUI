"""Exposure summary for a portfolio's location file: key figures, a map and TIV breakdowns."""
import streamlit as st

from pages.components.display import MapView
from pages.components.output import summarise_locations, valid_locations

TIV_COLUMNS = ['BuildingTIV', 'OtherTIV', 'ContentsTIV', 'BITIV']
BREAKDOWN_FIELDS = ['CountryCode', 'OccupancyCode', 'ConstructionCode', 'LocPerilsCovered']


def exposure_metrics(locations):
    summary = summarise_locations(locations).iloc[0]
    cols = st.columns(4)
    cols[0].metric('Locations', f"{int(summary['number_locations']):,}")
    cols[1].metric('Total TIV', f"{summary['TotalTIV']:,.0f}",
                   help='Total insured value: building, contents, other and business interruption.')
    if 'CountryCode' in locations:
        cols[2].metric('Countries', locations['CountryCode'].nunique())
    if 'LocPerilsCovered' in locations:
        cols[3].metric('Peril codes', locations['LocPerilsCovered'].nunique())


def exposure_map(locations):
    if {'Latitude', 'Longitude', 'BuildingTIV'} <= set(locations.columns) and valid_locations(locations):
        MapView(locations, weight='BuildingTIV', map_type='heatmap').display()
    elif {'CountryCode', 'BuildingTIV'} <= set(locations.columns):
        MapView(locations, weight='BuildingTIV', map_type='choropleth').display()
    else:
        st.caption('No coordinates or country codes to map.')


def exposure_breakdowns(locations):
    tiv_cols = [c for c in TIV_COLUMNS if c in locations]
    for field in BREAKDOWN_FIELDS:
        if field in locations and tiv_cols:
            st.markdown(f'**TIV by {field}**')
            breakdown = (locations.groupby(field)[tiv_cols].sum()
                         .assign(Locations=locations.groupby(field).size())
                         .sort_values(tiv_cols[0], ascending=False).reset_index())
            st.dataframe(breakdown, hide_index=True, height=200)


def exposure_overview(locations, breakdowns=True):
    """Key figures, a map and (optionally) TIV breakdowns for a location file."""
    exposure_metrics(locations)
    if breakdowns:
        map_col, breakdown_col = st.columns([0.6, 0.4])
        with map_col:
            exposure_map(locations)
        with breakdown_col:
            exposure_breakdowns(locations)
    else:
        exposure_map(locations)
