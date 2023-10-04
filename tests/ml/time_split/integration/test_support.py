import logging

import pandas as pd
import pytest

from rics.ml.time_split.integration._log_progress import handle_log_progress_arg
from rics.ml.time_split.types import DatetimeSplitBounds, DatetimeSplits


@pytest.mark.parametrize(
    "arg, name",
    [
        (True, "rics.ml.time_split"),
        ("handle-log-progress-arg", "handle-log-progress-arg"),
    ],
)
def test_handle_log_progress_arg(arg, name, caplog):
    _run(arg, name, caplog)


def test_logger_adapter(caplog):
    # Custom adapter class until https://github.com/python/cpython/pull/107292
    arg = logging.LoggerAdapter(logging.getLogger("test-logger-adapter"), extra={"foo": "bar"})
    _run(arg, "test-logger-adapter", caplog)
    for record in caplog.records:
        assert record.foo == "bar"


def _run(arg, name, caplog):
    splits: DatetimeSplits = [
        DatetimeSplitBounds(*map(pd.Timestamp, [f"1991-{i}", f"1999-{i}", f"2019-{i}"])) for i in [2, 4, 6]
    ]
    assert handle_log_progress_arg(False, splits=splits) is None
    tracked_splits = handle_log_progress_arg(arg, splits=splits)
    assert tracked_splits is not None
    assert len(list(tracked_splits)) == len(splits)
    assert len(caplog.records) == 2 * len(splits)
    for i, record in enumerate(caplog.records):
        fold = splits[i // 2]
        assert fold.start.isoformat() == record.start
        assert fold.mid.isoformat() == record.mid
        assert fold.end.isoformat() == record.end
        assert record.name == name
