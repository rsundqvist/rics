import warnings

import numpy as np
import pandas as pd
import pytest

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=UserWarning)
    from rics.mapping import Cardinality, support


@pytest.mark.parametrize("crash", [True, False])
def test_enable_verbose_debug_messages(crash):
    from rics.mapping import filter_functions, heuristic_functions, score_functions

    before = False, True, False
    filter_functions.VERBOSE, heuristic_functions.VERBOSE, score_functions.VERBOSE = before

    with support.enable_verbose_debug_messages():
        assert all((filter_functions.VERBOSE, heuristic_functions.VERBOSE, score_functions.VERBOSE))

    assert (filter_functions.VERBOSE, heuristic_functions.VERBOSE, score_functions.VERBOSE) == before


@pytest.mark.parametrize(
    "cardinality, min_score, expected",
    [
        (Cardinality.OneToOne, 0, {3: ("c4",), 2: ("c3",), 1: ("c2",), 0: ("c1",)}),
        (Cardinality.OneToOne, 10, {3: ("c4",), 2: ("c3",)}),
        (Cardinality.OneToMany, 0, {3: ("c4", "c3", "c2", "c1", "c0")}),
        (Cardinality.OneToMany, 10, {3: ("c4", "c3", "c2", "c1", "c0")}),
        (Cardinality.ManyToOne, 0, {3: ("c4",), 2: ("c4",), 1: ("c4",), 0: ("c4",)}),
        (Cardinality.ManyToOne, 10, {3: ("c4",), 2: ("c4",)}),
        (
            Cardinality.ManyToMany,
            0,
            {
                3: ("c4", "c3", "c2", "c1", "c0"),
                2: ("c4", "c3", "c2", "c1", "c0"),
                1: ("c4", "c3", "c2", "c1", "c0"),
                0: ("c4", "c3", "c2", "c1", "c0"),
            },
        ),
        (Cardinality.ManyToMany, 10, {3: ("c4", "c3", "c2", "c1", "c0"), 2: ("c4", "c3", "c2", "c1", "c0")}),
    ],
)
def test_natural_number_mapping(cardinality, min_score, expected):
    score = pd.DataFrame(np.arange(0, 20).reshape((4, -1)))
    score.columns = list(map("c{}".format, score))
    score.columns.name = "candidates"
    score.index.name = "values"
    actual = support.MatchScores(score, min_score).to_directional_mapping(cardinality).left_to_right
    assert actual == expected
