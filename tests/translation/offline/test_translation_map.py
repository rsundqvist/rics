def test_copy(translation_map):
    c = translation_map.copy()

    assert c.fmt == translation_map.fmt
    assert c.default_fmt == translation_map.default_fmt
    assert c.default_fmt_placeholders == translation_map.default_fmt_placeholders
    assert len(c) == len(translation_map)
    assert all(left == right for left, right in zip(c, translation_map))
