'''
Standalone script for AppTest coverage of `eltcalc_map`'s heatmap
branch when the output's `LocNumber` values have no overlap at all
with the location file's - this should warn instead of silently
rendering a map with every point at NaN lat/lon.
'''
import pandas as pd

from pages.components.output import eltcalc_map

map_df = pd.DataFrame({
    'LocNumber': [99, 100],
    'MeanLoss': [10.0, 20.0],
})

locations = pd.DataFrame({
    'LocNumber': [1, 2],
    'Longitude': [2.0, 2.5],
    'Latitude': [46.0, 46.5],
})

eltcalc_map(map_df, locations, oed_fields=['LocNumber'], map_type='heatmap',
           intensity_col='MeanLoss')
