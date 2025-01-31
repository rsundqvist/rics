import matplotlib.pyplot as plt
import numpy as np
import pytest

from rics.plotting import _PiTickHelper, pi_ticks

PI = _PiTickHelper.PI
HALF_PI = PI / 2


@pytest.mark.parametrize("half", ("frac", "dec", None))
def test_pi_ticks_doesnt_crash(half):
    ax = plt.axes()
    ax.plot(range(10))
    pi_ticks(ax, half)
    plt.close("all")


@pytest.mark.parametrize(
    "half, start, start_rounded_to_pi, expected",
    [
        ("frac", 0.0, 0, ["0/2π", "1/2π", "2/2π", "3/2π"]),
        ("dec", 0.0, 0, ["0.0π", "0.5π", "1.0π", "1.5π"]),
        (None, 0.0, 0, ["0", "π", "2π", "3π"]),
        ("frac", 1.0, HALF_PI, ["1/2π", "2/2π", "3/2π", "4/2π"]),
        ("dec", 1.5, HALF_PI, ["0.5π", "1.0π", "1.5π", "2.0π"]),
        (None, 0.5, 0, ["0", "π", "2π", "3π"]),
        ("dec", 3.5, PI, ["1.0π", "1.5π", "2.0π", "2.5π"]),
        (None, 8.5, 3 * PI, ["3π", "4π", "5π", "6π"]),
    ],
)
def test_pi_tick_helper(half, start, start_rounded_to_pi, expected):
    assert len(expected) == 4, "Bad test case"

    helper = _PiTickHelper(half, start=start)

    # Test locating
    values = [(start_rounded_to_pi + i * PI * (0.5 if half else 1), i) for i in range(4)]
    v2 = [(x, i) for i, x in enumerate(helper.locator.tick_values(start, 100)[:4])]
    assert np.allclose(values, v2)

    # Test formatting
    actual = [helper._format(x, pos) for x, pos in values]
    assert actual == expected
