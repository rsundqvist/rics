from collections import defaultdict
from typing import Any, assert_type

import pandas as pd
import pytest

from rics.performance import MultiCaseTimer, to_dataframe


def generate_data(size: int, dtype: str, **kwargs: Any) -> pd.Series:
    return pd.Series([1, 2, 3]).astype(dtype).sample(size, **kwargs)


@pytest.mark.filterwarnings("ignore:Results may be unreliable:UserWarning")
def test_generated_data():
    counts: dict[tuple[int, str], int] = defaultdict(int)

    def generate_data_with_counts(size: int, dtype: str, **kwargs: Any) -> pd.Series:
        nonlocal counts
        counts[(size, dtype)] += 1
        return generate_data(size, dtype, **kwargs)

    timer = MultiCaseTimer(
        pd.Series.describe,
        generate_data_with_counts,
        case_args=[
            (1, "int32"),
            (5, "int32"),
            (5, "str"),
        ],
        kwargs={"replace": True},
    )

    repeat = 3
    number = 2
    results = timer.run(repeat=repeat, number=number)
    df = to_dataframe(results, names=timer.derive_names())
    assert df.dtypes["dtype"] == "object"
    assert df.dtypes["size"] == "int"
    assert len(df) == repeat * 3

    assert counts == {(1, "int32"): 1, (5, "int32"): 1, (5, "str"): 1}


class TestDeriveNames:
    def test_derive_names(self):
        timer = MultiCaseTimer(pd.Series.describe, generate_data, case_args=[(1, "int32")])
        assert timer.derive_names() == ["size", "dtype"]


class TestErrors:
    def test_not_callable(self):
        timer: MultiCaseTimer[str] = MultiCaseTimer(pd.Series.describe, test_data={"not": "callable"})

        with pytest.raises(TypeError, match="callable `test_data`"):
            assert timer.derive_names()

    def test_no_enough_positional_arguments(self):
        case_arg0 = (0, 1, 2, 3)

        timer = MultiCaseTimer(
            pd.Series.describe,
            generate_data,  # type: ignore[arg-type]
            case_args=[
                case_arg0,
            ],
        )
        assert_type(timer, MultiCaseTimer[Any, int, int, int, int])  # Determined by the case list

        with pytest.raises(RuntimeError, match=f"at least {len(case_arg0)}"):
            assert timer.derive_names()

    @pytest.mark.parametrize("test_data", [generate_data, {}])
    def test_no_cases(self, test_data):
        with pytest.raises(ValueError, match=r"No case data given."):
            MultiCaseTimer(pd.Series.describe, test_data)

    @pytest.mark.parametrize(
        "case_args, kwargs",
        [
            [(1,), None],
            [None, {1: 1}],
            [(1,), {1: 1}],
        ],
        ids=["args", "kwargs", "both"],
    )
    def test_forbidden_with_dict(self, case_args, kwargs):
        test_data = {"not": "callable"}
        match = "Cannot pass `case_args` or `kwargs` when `test_data` is not a callable."
        with pytest.raises(TypeError, match=match):
            MultiCaseTimer(
                pd.Series.describe,
                test_data,
                case_args=case_args,
                kwargs=kwargs,
            )
