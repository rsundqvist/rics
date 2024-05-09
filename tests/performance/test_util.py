import pytest
from rics.performance._util import _import_context


def test_import_missing():
    with pytest.raises(ImportError, match=r"rics\[all\]"):
        _import_missing()


def _import_missing():
    with _import_context("package-name"):
        import does_not_exist  # type: ignore[import-not-found]

        does_not_exist.dont_delete_me()
