from rics.utility.collections import misc


def test_as_list():
    assert ["123"] == misc.as_list("123")
    assert ["123"] == misc.as_list(["123"])  # type: ignore[arg-type]
    assert list("123") == misc.as_list(list("123"))  # type: ignore[arg-type]
    assert list("123") == misc.as_list("123", excl_types=(int,))
