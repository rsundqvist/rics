import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pytest

from rics.performance import MultiCaseTimer, plot_run, to_dataframe
from rics.performance.types import ResultsDict

NAMES = ["n_units", "unit"]

pytestmark = [
    pytest.mark.filterwarnings("ignore:Results may be unreliable:UserWarning"),
]


@pytest.mark.skipif(sys.platform == "win32", reason="Issue with the mu character.")
def test_to_dataframe():
    run_results = get_run_results()
    df = to_dataframe(run_results, names=NAMES)

    assert NAMES[0] in df.columns
    assert NAMES[1] in df.columns

    actual = df.to_string(float_format="%2.2g")
    expected = Path(__file__).parent.joinpath("expected-with-names.fwf").read_text()
    assert actual == expected


def test_run_output():
    """Doesn't really belong here (doesn't use NAMES), but confirms that get_run_results() still makes sense."""

    timer: MultiCaseTimer[float] = MultiCaseTimer(
        candidate_method={"sleep_x1": lambda _: None, "sleep_x4": lambda _: None},  # For speed. Real is time.sleep(s)
        test_data={(1, "ms"): 0.001, (2, "ms"): 0.001, (5_000_000, "ns"): 0.001},
    )
    run_results = timer.run(repeat=2, number=1)

    actual_shape = {
        candidate_label: {data_label: len(data_results) for data_label, data_results in candidate_results.items()}
        for candidate_label, candidate_results in run_results.items()
    }

    assert actual_shape == {
        "sleep_x1": {(1, "ms"): 2, (2, "ms"): 2, (5000000, "ns"): 2},
        "sleep_x4": {(1, "ms"): 2, (2, "ms"): 2, (5000000, "ns"): 2},
    }


class TestPlotNames:
    def test_dicts(self):
        self.run(get_run_results())

    def test_frame_without_names(self):
        run_results = get_run_results()
        df = to_dataframe(run_results, names=[])
        self.run(df)

    def test_frame_with_names(self):
        run_results = get_run_results()
        df = to_dataframe(run_results, names=NAMES)
        self.run(df)

    @classmethod
    def run(cls, run_results):
        g = plot_run(run_results, unit="us", log_scale=True, names=NAMES, aspect=4)
        assert g.ax.get_xlabel() == "Test data"
        assert g.ax.get_ylabel() == "Time [μs]"
        assert [text.get_text() for text in g.ax.get_xticklabels()] == [
            "n_units = 1 | unit = ms",
            "n_units = 2 | unit = ms",
            "n_units = 5000000 | unit = ns",
        ]

        assert [text.get_text() for text in g.legend.texts] == [
            "sleep_x1",
            "sleep_x4",
        ]

        assert tuple(g.figure.get_size_inches()) >= (18, 4.00), "figure too small"
        plt.close(g.figure)


def get_run_results() -> ResultsDict:
    return {
        "sleep_x1": {
            (1, "ms"): [0.002964, 0.002791],
            (2, "ms"): [0.005155, 0.005601],
            (5000000, "ns"): [0.012693, 0.013457],
        },
        "sleep_x4": {
            (1, "ms"): [0.011636, 0.010197],
            (2, "ms"): [0.020328, 0.020775],
            (5000000, "ns"): [0.050241, 0.050206],
        },
    }
