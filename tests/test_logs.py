import logging

import pytest

from rics.logs import basic_config


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
