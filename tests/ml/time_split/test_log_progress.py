import pytest

from rics.ml.time_split import log_split_progress, settings, split


@pytest.mark.parametrize("extra", ["{{escaped-key}}", "{extra0}", "{extra1}", "{extra1} and {extra1}!"])
def test_log_progress(extra, caplog, monkeypatch):
    monkeypatch.setattr(
        settings.log_split_progress,
        "START_MESSAGE",
        settings.log_split_progress.START_MESSAGE + f"\n{extra}, mutable={{mutable}}",
    )

    user_extra = {"extra0": 0, "extra1": 1, "mutable": "a"}
    for i, _ in enumerate(
        log_split_progress(split(["2022-1", "2022-2", "2022-3"], after="1d"), extra=user_extra), start=1
    ):
        record = caplog.records[-1]
        must_contain = extra.format(**user_extra)
        assert record.message.startswith("Begin fold")
        assert must_contain in record.message
        assert record.extra0 == 0
        assert record.extra1 == 1
        assert record.mutable == "a" * i

        user_extra["mutable"] = "a" * (i + 1)

    assert user_extra == {"extra0": 0, "extra1": 1, "mutable": "aaaa"}
