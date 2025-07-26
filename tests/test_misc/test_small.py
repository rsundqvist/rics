import pickle

from rics import misc


def test_get_local_or_remote(tmp_path):
    def my_postprocessor(_):
        return ["my-data", {"is": "amazing"}]

    remote_root = "doesn't exist"

    tmp_path.joinpath("foo.txt").write_text("test")

    path = misc.get_local_or_remote("foo.txt", remote_root=remote_root, local_root=tmp_path)
    assert path == tmp_path.joinpath("foo.txt")

    path = misc.get_local_or_remote(
        "foo.txt", remote_root=remote_root, local_root=tmp_path, postprocessor=my_postprocessor
    )
    assert path == tmp_path / "my_postprocessor/foo.pkl"

    with path.open("rb") as f:
        actual = pickle.load(f)
    assert actual == ["my-data", {"is": "amazing"}]


def test_serializable():
    def foo():
        pass

    assert not misc.serializable(foo)
    assert misc.serializable(misc.serializable)
