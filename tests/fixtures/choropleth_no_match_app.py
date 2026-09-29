'''
Standalone script for AppTest coverage of `MapView.generate_choropleth`
when the output's `CountryCode` values have no overlap at all with the
geojson's `iso_a2` values - this should warn instead of silently
computing a NaN center from an empty geometry join.
'''
import pandas as pd

from pages.components.display import MapView

map_df = pd.DataFrame({
    'CountryCode': ['ZZ', 'ZZ'],
    'MeanLoss': [10.0, 20.0],
})

mv = MapView(map_df, weight='MeanLoss', map_type='choropleth')
mv.display()
