import pytest

from rics.performance import format_perf_counter, format_seconds, relative_to, to_dataframe
from rics.performance.types import ResultsDict

RESULTS: ResultsDict = {
    "baseline": {("g", 1): [1.0, 1.2], ("g", 2): [2.0, 2.4]},
    "fast": {("g", 1): [0.5, 0.6], ("g", 2): [0.5, 0.7]},
}


class TestRelativeTo:
    def test_speedup(self):
        df = relative_to(RESULTS, baseline="baseline", names=["grp", "n"], agg="min")
        fast = df[df["candidate"] == "fast"].set_index("n")
        # baseline min: n1=1.0, n2=2.0 ; fast min: n1=0.5, n2=0.5
        assert fast.loc[1, "speedup"] == pytest.approx(2.0)
        assert fast.loc[2, "speedup"] == pytest.approx(4.0)
        base = df[df["candidate"] == "baseline"]
        assert (base["speedup"] == 1.0).all()

    def test_geomean_attr(self):
        df = relative_to(RESULTS, baseline="baseline", names=["grp", "n"])
        assert df.attrs["geomean"]["fast"] == pytest.approx((2.0 * 4.0) ** 0.5)
        assert df.attrs["geomean"]["baseline"] == pytest.approx(1.0)

    def test_accepts_dataframe(self):
        frame = to_dataframe(RESULTS, names=["grp", "n"])
        df = relative_to(frame, baseline="baseline", names=["grp", "n"])
        assert df[df["candidate"] == "fast"]["speedup"].min() == pytest.approx(2.0)

    def test_bad_baseline(self):
        with pytest.raises(KeyError, match="nope"):
            relative_to(RESULTS, baseline="nope", names=["grp", "n"])

    def test_bad_agg(self):
        with pytest.raises(TypeError, match="agg"):
            relative_to(RESULTS, baseline="baseline", agg="p99")  # type: ignore[arg-type]


class TestDeprecated:
    def format_perf_counter(self):
        with pytest.warns(DeprecationWarning, match="format_perf_counter"):
            actual = format_perf_counter(0, 7794363.9)
        assert actual == "90d 5h 6m 4s"

    def test_seconds(self):
        with pytest.warns(DeprecationWarning, match="format_seconds"):
            actual = format_seconds(7794363.9)
        assert actual == "90d 5h 6m 4s"
