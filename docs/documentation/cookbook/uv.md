# uv

## MyPy `--install-types` without `pip`
The `--install-types` flag requires `pip`. To add manually without version constraints:

```bash
cat .mypy_cache/missing_stubs  # show what will be added
uv add -r .mypy_cache/missing_stubs --group=types --raw-sources
```

Where `--raw-sources` avoids locking specific versions. This is a hack. No official solution exists yet;
see https://github.com/python/mypy/issues/10600.
