'''
AppTest-based coverage for the ORD render fragments in
`pages/components/output.py`. Each fragment is exercised via a small
standalone script under `tests/fixtures/` (rather than the full
app/login stack), built around a synthetic output DataFrame using the
PascalCase column names the fragments assume ktools produces (see
`OutputInterface`'s docstring and the "Important caveat" in the
project's ORD visualisation plan: there are no sample ktools output
fixtures checked into this repo, so these assumptions are not yet
validated against a real analysis run).
'''
from streamlit.testing.v1 import AppTest


def test_selt_fragment_renders_table_and_map():
    at = AppTest.from_file("tests/fixtures/selt_fragment_app.py").run()

    assert len(at.exception) == 0
    assert [t.label for t in at.tabs] == ["Table", "Map"]
    assert len(at.dataframe) == 1
    assert len(at.get("plotly_chart")) == 1


def test_splt_fragment_renders_bar_chart():
    at = AppTest.from_file("tests/fixtures/splt_fragment_app.py").run()

    assert len(at.exception) == 0
    assert len(at.get("plotly_chart")) == 1


def test_alct_fragment_renders_table():
    at = AppTest.from_file("tests/fixtures/alct_fragment_app.py").run()

    assert len(at.exception) == 0
    assert len(at.dataframe) == 1
    assert set(at.dataframe[0].value["SummaryId"]) == {1, 2}


def test_psept_fragment_renders_ep_curve():
    at = AppTest.from_file("tests/fixtures/psept_fragment_app.py").run()

    assert len(at.exception) == 0
    assert len(at.get("plotly_chart")) == 1


def test_qplt_and_ept_fragments_coexist_without_widget_key_collision():
    '''
    Regression test: `generate_ept_fragment` used to reuse
    `generate_qplt_fragment`'s OED-field pills key
    (`qplt_{p}_group_field_pills`) and had no key at all on its EP
    Curve Type / Calculation Method radios, so rendering both QPLT and
    EPT for the same perspective raised a Streamlit
    duplicate-widget-key error.
    '''
    at = AppTest.from_file("tests/fixtures/qplt_ept_regression_app.py").run()

    assert len(at.exception) == 0
    assert len(at.get("plotly_chart")) == 2


def test_eltcalc_map_heatmap_survives_locnumber_dtype_mismatch():
    '''
    Regression test: `eltcalc_map`'s heatmap branch merged the ORD
    output's `LocNumber` (joined in from the ktools summary-info file)
    against the location file's `LocNumber` without normalising
    either side's dtype first. A str-vs-int mismatch between the two
    (same values, different dtype) used to merge to all-NaN
    Longitude/Latitude silently, rendering a map with nothing visible
    on it - the exact "map view isn't working" symptom this pins.
    '''
    at = AppTest.from_file("tests/fixtures/eltcalc_map_locnumber_mismatch_app.py").run()

    assert len(at.exception) == 0
    assert len(at.warning) == 0
    assert len(at.get("plotly_chart")) == 1


def test_eltcalc_map_heatmap_warns_when_no_locations_match():
    '''
    When the output's LocNumber values have no overlap at all with the
    location file (a real data problem, not a dtype mismatch), warn
    instead of silently rendering a map with every point at NaN.
    '''
    at = AppTest.from_file("tests/fixtures/eltcalc_map_no_match_app.py").run()

    assert len(at.exception) == 0
    assert len(at.warning) == 1
    assert len(at.get("plotly_chart")) == 0


def test_choropleth_survives_countrycode_case_mismatch():
    '''
    Regression test: `MapView.generate_choropleth` merged the output's
    `CountryCode` against the geojson's `iso_a2` without normalising
    either side first. A case mismatch between the two ('fr' vs 'FR' -
    same country, different formatting) used to merge to no rows
    silently, same failure class as the LocNumber/heatmap one above.
    '''
    at = AppTest.from_file("tests/fixtures/choropleth_countrycode_mismatch_app.py").run()

    assert len(at.exception) == 0
    assert len(at.warning) == 0
    assert len(at.get("plotly_chart")) == 1


def test_choropleth_warns_when_no_countries_match():
    '''
    When the output's CountryCode values don't correspond to any
    country in the geojson (a real data problem), warn instead of
    silently computing a NaN center from an empty geometry join.
    '''
    at = AppTest.from_file("tests/fixtures/choropleth_no_match_app.py").run()

    assert len(at.exception) == 0
    assert len(at.warning) == 1
    assert len(at.get("plotly_chart")) == 0
