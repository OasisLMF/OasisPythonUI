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
