import logging

import pytest

ROOT_LEVEL = logging.root.level
HANDLER = logging.NullHandler()
logging.getLogger("existing").addHandler(HANDLER)


@pytest.mark.usefixtures("restore_logging")
def test_mutate():
    logging.basicConfig(level=logging.CRITICAL, force=True)
    existing = logging.getLogger("existing")
    existing.setLevel(logging.DEBUG)
    existing.propagate = False
    existing.handlers.clear()
    logging.getLogger("new").setLevel(logging.ERROR)
    logging.disable(logging.INFO)


def test_restored():
    existing = logging.getLogger("existing")
    assert (existing.level, existing.propagate, existing.handlers) == (logging.NOTSET, True, [HANDLER])
    assert logging.getLogger("new").level == logging.NOTSET
    assert logging.root.level == ROOT_LEVEL
    assert logging.root.manager.disable == logging.NOTSET
