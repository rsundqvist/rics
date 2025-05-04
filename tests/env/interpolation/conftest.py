from os import environ


def set_variables(*ids: int) -> dict[str, str]:
    expected = {}

    for var_name in list(environ):
        if var_name.startswith("ENV_VAR"):
            del environ[var_name]
    for i in ids:
        environ[f"ENV_VAR{i}"] = f"VALUE{i}"
        expected[f"ENV_VAR{i}"] = f"VALUE{i}"

    return expected
