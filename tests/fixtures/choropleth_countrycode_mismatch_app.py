'''
Standalone script for AppTest coverage of `MapView.generate_choropleth`
when the output's `CountryCode` values and the geojson's `iso_a2`
values differ only in case (e.g. 'fr' vs 'FR') - this used to merge to
no matches silently.
'''
import pandas as pd

from pages.components.display import MapView

map_df = pd.DataFrame({
    'CountryCode': ['fr', 'fr'],
    'MeanLoss': [10.0, 20.0],
})

mv = MapView(map_df, weight='MeanLoss', map_type='choropleth')
mv.display()
