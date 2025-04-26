import logging

import pytest

from rics.logs import (
    LoggingSetupHelper,
    LogLevelError,
    _extract_extra_levels,
    basic_config,
    convert_log_level,
    disable_temporarily,
)

logging.addLevelName(1, "EXTRA_VERBOSE_DEBUG")


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
        [
            logging.LoggerAdapter(logging.getLogger("rics"), extra={}),
            logging.getLogger("id_translation"),
        ],
    ],
)
def test_disable_temporarily(loggers, caplog):
    def log_messages():
        caplog.clear()
        for i, logger in enumerate(loggers):
            if isinstance(logger, str):
                logger = logging.getLogger(logger)  # noqa: PLW2901
            logger.warning("Hello from logger #%i of type %r!", i, type(logger).__name__)
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
    actual = next(iter(_extract_extra_levels(**{f"{arg}_level": logging.INFO})[0]))
    assert actual == expected.replace(":", ".")


class TestLoggingSetupHelper:
    @pytest.fixture
    def helper(self) -> LoggingSetupHelper:
        levels: list[dict[str, str | int]] = [
            {"rics": "INFO", "root": logging.WARNING, "id_translation": logging.INFO},
            {"rics.jupyter": "DEBUG", "id_translation": "DEBUG"},
            {"root": logging.DEBUG, "rics.jupyter": "EXTRA_VERBOSE_DEBUG"},
            {"rics": 5},
        ]
        return LoggingSetupHelper(levels)

    class TestBadLevels:
        def test_empty_list(self):
            with pytest.raises(TypeError) as exc_info:
                LoggingSetupHelper([])
            assert exc_info.value.args[0] == "No levels given."

        def test_empty_dict(self):
            with pytest.raises(TypeError) as exc_info:
                LoggingSetupHelper([{"rics": logging.INFO}, {}])
            assert exc_info.value.args[0] == "Level 2 (index=1): No items."

        def test_same(self):
            with pytest.raises(ValueError) as exc_info:
                LoggingSetupHelper([{"rics": logging.INFO}, {"rics": logging.INFO}])
            exc_info.value.args[0].startswith(
                "Level 2 (index=1), logger='rics': Found transition 'INFO (20) -> INFO (20)'."
            )

        def test_lower(self):
            with pytest.raises(ValueError) as exc_info:
                LoggingSetupHelper([{"rics": logging.INFO}, {"rics": "WARN"}])
            assert exc_info.value.args[0].startswith(
                "Level 2 (index=1), logger='rics': Found transition 'INFO (20) -> WARNING (30)'."
            )

    class TestFormatting:
        def test_by_log_level(self, helper):
            assert helper._by_log_level() == [
                {20: ["id_translation", "rics"], 30: ["root"]},
                {10: ["id_translation", "rics.jupyter"], 20: ["rics"], 30: ["root"]},
                {1: ["rics.jupyter"], 10: ["id_translation", "root"], 20: ["rics"]},
                {1: ["rics.jupyter"], 5: ["rics"], 10: ["id_translation", "root"]},
            ]

        def test_get_verbosity_lines(self, helper):
            assert helper.get_level_descriptions() == [
                "id_translation & rics: INFO (20), root: WARNING (30)",
                "id_translation & rics.jupyter: DEBUG (10)",
                "rics.jupyter: EXTRA_VERBOSE_DEBUG (1), root: DEBUG (10)",
                "rics: <no name> (5)",
            ]


class TestBadLogLevel:
    def test_unknown_int(self):
        name = self.test_unknown_int.__name__ + "_log_level"

        with pytest.raises(LogLevelError) as exc_info:
            convert_log_level(5, name=name, verify=True)

        assert str(exc_info.value) == f"Unknown {name}=5."
        assert exc_info.value.argument_name
        assert exc_info.value.log_level == 5
        assert exc_info.value.__notes__ == [
            "Hint: Set `verify=False` to allow.",
            "Hint: Register this level using `logging.addLevelName()`",
        ]

    def test_unknown_str(self):
        name = self.test_unknown_str.__name__ + "_log_level"

        with pytest.raises(LogLevelError) as exc_info:
            convert_log_level("Unknown", name=name, verify=True)

        assert str(exc_info.value) == f"Unknown {name}='Unknown'."
        assert exc_info.value.argument_name
        assert exc_info.value.log_level == "Unknown"
        assert exc_info.value.__notes__ == ["Hint: Register this level using `logging.addLevelName()`"]

    def test_upper_str(self):
        name = self.test_upper_str.__name__ + "_log_level"

        with pytest.raises(LogLevelError) as exc_info:
            convert_log_level("info", name=name, verify=True)

        assert str(exc_info.value) == f"Unknown {name}='info'."
        assert exc_info.value.argument_name
        assert exc_info.value.log_level == "info"
        assert exc_info.value.__notes__ == [
            f"Hint: Did you mean {name}='INFO'?",
            "Hint: Register this level using `logging.addLevelName()`",
        ]
