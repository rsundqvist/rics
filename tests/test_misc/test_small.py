import pickle

import pytest
import requests
import responses

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


@responses.activate
def test_get_local_or_remote_http_error(tmp_path):
    responses.get("https://example.com/foo.txt", status=404, body="Not Found")

    with pytest.raises(requests.HTTPError):
        misc.get_local_or_remote("foo.txt", remote_root="https://example.com", local_root=tmp_path)
    assert not tmp_path.joinpath("foo.txt").exists()


def test_serializable():
    def foo():
        pass

    assert not misc.serializable(foo)
    assert misc.serializable(misc.serializable)
