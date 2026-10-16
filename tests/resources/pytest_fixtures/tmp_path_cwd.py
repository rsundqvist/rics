from pathlib import Path

CWD = Path.cwd()


def test_chdir(tmp_path_cwd, tmp_path):
    assert Path.cwd() == tmp_path_cwd == tmp_path


def test_restored():
    assert Path.cwd() == CWD
