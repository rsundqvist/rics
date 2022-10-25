import logging

from rics.utility.logs import basic_config


def test_set_levels():
    basic_config(
        level=logging.CRITICAL,
        rics_level=logging.INFO,
        rics_utility_level=logging.DEBUG,
        foo_level=logging.WARNING,
        foo_bar_level=logging.INFO,
    )

    assert logging.getLogger().getEffectiveLevel() == logging.CRITICAL, "root"

    assert logging.getLogger("alib").getEffectiveLevel() == logging.CRITICAL, "alib"
    assert logging.getLogger("alib.submodule").getEffectiveLevel() == logging.CRITICAL, "alib.submodule"

    assert logging.getLogger("rics").getEffectiveLevel() == logging.INFO, "rics"
    assert logging.getLogger("rics.submodule").getEffectiveLevel() == logging.INFO, "rics.submodule"
    assert logging.getLogger("rics.utility").getEffectiveLevel() == logging.DEBUG, "rics.utility"

    assert logging.getLogger("foo").getEffectiveLevel() == logging.WARNING, "foo"
    assert logging.getLogger("foo.submodule").getEffectiveLevel() == logging.WARNING, "foo.submodule"
    assert logging.getLogger("foo.bar").getEffectiveLevel() == logging.INFO, "foo.bar"
