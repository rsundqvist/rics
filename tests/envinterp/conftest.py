from os import environ
from typing import Dict


def set_variables(*ids: int) -> Dict[str, str]:
    ans = {}

    for var_name in list(environ):
        if var_name.startswith("ENV_VAR"):
            del environ[var_name]
    for i in ids:
        environ[f"ENV_VAR{i}"] = f"VALUE{i}"
        ans[f"ENV_VAR{i}"] = f"VALUE{i}"

    return ans
