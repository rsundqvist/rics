import pytest

from rics.performance import format_perf_counter, format_seconds, to_dataframe
from rics.performance.types import ResultsDict

RESULTS: ResultsDict = {
    "baseline": {("g", 1): [1.0, 1.2], ("g", 2): [2.0, 2.4]},
    "fast": {("g", 1): [0.5, 0.6], ("g", 2): [0.5, 0.7]},
}


class TestToDataFrameTidy:
    def test_columns(self):
        df = to_dataframe(RESULTS, names=["grp", "n"], tidy=True)
        assert list(df.columns) == ["candidate", "data", "grp", "n", "run", "seconds"]
        # No presentation/derived columns.
        assert not [c for c in df.columns if c.startswith("Time [")]

    def test_values(self):
        df = to_dataframe(RESULTS, names=["grp", "n"], tidy=True)
        row = df[(df["candidate"] == "fast") & (df["n"] == 1) & (df["run"] == 0)].iloc[0]
        assert row["seconds"] == 0.5
        assert row["grp"] == "g"


class TestDeprecated:
    def format_perf_counter(self):
        with pytest.warns(DeprecationWarning, match="format_perf_counter"):
            actual = format_perf_counter(0, 7794363.9)
        assert actual == "90d 5h 6m 4s"

    def test_seconds(self):
        with pytest.warns(DeprecationWarning, match="format_seconds"):
            actual = format_seconds(7794363.9)
        assert actual == "90d 5h 6m 4s"
