import pytest

from rics.translation.fetching import support
from rics.translation.fetching.exceptions import ImplementationError
from rics.translation.fetching.types import FetchInstruction


def test_bad_implementation():
    with pytest.raises(ImplementationError):
        support.from_records(
            FetchInstruction(
                "source",
                [1, 2, 3],
                ("id",),
                {
                    "id",
                },
                False,
            ),
            ("id",),
            [],
        )
