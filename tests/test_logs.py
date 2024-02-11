import logging

import pytest

from rics.logs import _extract_extra_levels, basic_config, disable_temporarily


@pytest.mark.skip(reason="Messes up logging for other tests.")
@pytest.mark.parametrize(
    "logger_name, level_name",
    [
        ("rics", "INFO"),
        ("id_translation", "DEBUG"),
        ("matplotlib", "WARNING"),
        ("random_lib", "CRITICAL"),
        ("another", "CRITICAL"),
    ],
)
def test_set_levels(logger_name, level_name):
    basic_config(level=logging.CRITICAL, id_translation_level=logging.DEBUG)
    assert logging.getLogger().getEffectiveLevel() == logging.CRITICAL, "Bad root level"

    expected_level = logging.getLevelName(level_name)
    assert logging.getLogger(logger_name).getEffectiveLevel() == expected_level


@pytest.mark.parametrize(
    "loggers",
    [
        [logging.root],
        ["rics", "id_translation"],
        [logging.LoggerAdapter(logging.root, extra={})],
        [logging.LoggerAdapter(logging.getLogger("rics"), extra={})],
        [logging.LoggerAdapter(logging.getLogger("rics"), extra={}), logging.getLogger("id_translation")],
    ],
)
def test_disable_temporarily(loggers, caplog):
    def log_messages():
        caplog.clear()
        for i, lgr in enumerate(loggers):
            if isinstance(lgr, str):
                lgr = logging.getLogger(lgr)
            lgr.warning("Hello from logger #%i of type %r!", i, type(lgr).__name__)
        return caplog.records

    actual = log_messages()
    expected = max(1, len(loggers))
    assert len(actual) == expected

    with disable_temporarily(*loggers):
        actual = log_messages()

    assert len(actual) == 0


@pytest.mark.parametrize(
    "arg, expected",
    [
        # Use ':' instead of '.' in expected to get prettier pytest output.
        ("_foo___bar", "_foo:_bar"),
        ("rics__performance", "rics:performance"),
        ("id_translation", "id_translation"),
        ("id_translation__fetching", "id_translation:fetching"),
        ("rics___internal_support", "rics:_internal_support"),
    ],
)
def test_extract_extra_levels(arg, expected):
    actual = list(_extract_extra_levels(**{f"{arg}_level": logging.INFO})[0])[0]
    assert actual == expected.replace(":", ".")
