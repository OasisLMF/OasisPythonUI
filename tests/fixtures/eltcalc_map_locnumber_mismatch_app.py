'''
Standalone script for AppTest coverage of `eltcalc_map`'s heatmap
branch when the output's `LocNumber` column and the location file's
`LocNumber` column have different dtypes (e.g. str vs int) but the
same underlying values - this used to merge to all-NaN silently.
'''
import pandas as pd

from pages.components.output import eltcalc_map

map_df = pd.DataFrame({
    'LocNumber': ['1', '2', '1', '2'],
    'MeanLoss': [10.0, 20.0, 15.0, 25.0],
})

locations = pd.DataFrame({
    'LocNumber': [1, 2],
    'Longitude': [2.0, 2.5],
    'Latitude': [46.0, 46.5],
})

eltcalc_map(map_df, locations, oed_fields=['LocNumber'], map_type='heatmap',
           intensity_col='MeanLoss')
