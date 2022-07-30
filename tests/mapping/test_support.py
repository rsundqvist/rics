import warnings

import pytest

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=UserWarning)
    from rics.mapping import support


@pytest.mark.parametrize("crash", [True, False])
def test_enable_verbose_debug_messages(crash):

    from rics.mapping import filter_functions, heuristic_functions, score_functions

    before = False, True, False
    filter_functions.VERBOSE, heuristic_functions.VERBOSE, score_functions.VERBOSE = before

    with support.enable_verbose_debug_messages():
        assert all((filter_functions.VERBOSE, heuristic_functions.VERBOSE, score_functions.VERBOSE))

    assert (filter_functions.VERBOSE, heuristic_functions.VERBOSE, score_functions.VERBOSE) == before
