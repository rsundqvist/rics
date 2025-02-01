# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [Unreleased]

## [5.0.0] - 2025-02-01

### Added
- Argument `include_module=False` for function `misc.tname()`.
- New function `plotting.percentage_ticks()`

### Fixed
- Handling of gh-101860 (new `@property.__name__`) under 3.13 in `misc.tname()` and `misc.get_public_module()`.

### Removed
- Module `rics.ml.time_split`. use the `time-split` [![PyPI - Version](https://img.shields.io/pypi/v/time-split.svg)](https://pypi.python.org/pypi/time-split) package instead.

## [4.1.1] - 2024-06-29

### Fixed
- Fix handling of `paths.parse_any_path()` bool-type postprocessors (raise on `False`).

## [4.1.0] - 2024-05-25

### Added
- New module `rics.paths`; `paths.parse_any_path()`, derived functions `any_path_to_str()` and `any_path_to_path()`.
- New module `rics.strings`. Moved `format_perf_counter()` and `format_seconds()`.
- New function `strings.format_bytes()`.
- New function `rics.collections.dicts.format_changed_keys()`.

### Deprecated
- Module `rics.ml.time_split`. use the `time-split` [![PyPI - Version](https://img.shields.io/pypi/v/time-split.svg)](https://pypi.python.org/pypi/time-split) package instead.
- Functions `rics.performance.format_perf_counter()` and `format_seconds()`. Use `rics.strings`-functions instead.

## [4.0.1] - 2024-03-21

### Fixed
- Fix RTD build. Docs for `4.0.0` are not available, but `4.0.1` docs are identical.

## [4.0.0] - 2024-03-21

### Added
- Python `3.12` is now fully tested and supported in CI/CD.
- New support module `time_split.integration.split_data`.
- New `time_split` integration: `integration.polars.split_polars`.

### Changed
- Python minimum version is now `3.11` (was `3.8`).
- The `time_split` Pandas integration no longer supports the `inclusive=left|right|neither` argument (now always `left`).
- Updates to `rics.performance`:
  * Functions and classes are  now generically typed.
  * Implement optional progress bars.
  * Added new plotting backend (**_experimental_**).
  * Select suitable time unit automatically when plotting (was: milliseconds).

### Removed
- Module `rics.mapping` was previously deprecated and has now been removed.
- Module `rics.pandas` was previously deprecated and has now been removed.
- Module `rics.strings` (use `str` methods instead).

## [3.3.0] - 2024-02-11

### Added
- The `get_by_full_name()` function has two new optional arguments `instance_of` and `subclass_of`, which may be 
  used to ensure correct return types.
- The `unflatten_dict()` function now supports `tuple` keys.
- The `logs.disable_temporarily()` function now support passing loggers by name.

### Fixed
- Print parent of inner class in `misc.tname()` when `prefix_classname=True`.
- Prefer later folds when using frequency-based schedule and after arguments (`ml.time_split`, #313).

## [3.2.0] - 2023-10-17

### Added
- Add new `step` argument to `ml.time_split` splitting functions.
- Add new `plot.REMOVED_FOLD_STYLE` attribute to `time_split.settings`.

### Fixed
- Update, fix and clarify some documentation issues.
- The `misc.tname()`-function now handles `functools.partial` properly (new argument `attrs='func'`).

## [3.1.0] - 2023-10-13

### Added
- New module `rics.ml.time_split`; successor to `pandas.TimeFold`.
- Function `collections.dicts.unflatten_dict()`; inverse of `flatten_dict()`.
- Function `misc.get_public_module()`; resolve public module name of an object, optionally looking for reexports.
- Function `misc.format_kwargs()`; pretty-print keyword arguments.

### Changed
- The `flatten_dict()`-function now takes a `string_fn`-argument (default=`str`).
- Update format used for durations in `rics.performance`.

### Deprecated
- The `rics.pandas.TimeFold` class. Replaced by `rics.ml.time_split`.

### Fixed
- Handle `LoggerAdapter` in `logs.disable_temporarily()`.
- Handle improve handling of '{}' (e.g. Python fstrings) in `envinterp`.
- Handle properties in `misc.tname`.

## [3.0.1] - 2023-03-25

### Changed
- Deprecated `rics.mapping`.

### Fixed
- Fixed some minor `TimeFold` issues.
- `TimeFold.make_sklearn_splitter.split` and `TimeFold.plot` now handle datetime-like iterables correctly.

## [3.0.0] - 2023-03-09

### Added
- The `score_functions.disabled()` function, used to force a `Mapper` to work in override-only mode.
- An optional argument `for_value` to the `heuristic_functions.value_fstring_alias()` function.
- The `Mapper.copy()`-method now accepts keyword override arguments.
- The `envinterp` module and `misc.interpolate_environment_variables()` function (replaces `read_env_or_literal()`)

### Changed
- Add `n_splits` argument to `TimeFold` (scikit-learn compatibility).
- Raise `AmbiguousScoreError` if match scores do not allow deterministic mapping.
- Add a small positional penalty in `HeuristicScore`, to favor alias functions that are defined early.
- Add a small positional penalty in `modified_hamming`, to favor candidates that are defined early.
- Reduce default value of `Mapper.min_score` (from 1.0 to 0.9).
- Updated `Mapper` verbosity flag to be consistent. Now called `verbose_logging` everywhere.

### Fixed
- The `heuristic_functions.candidate_fstring_alias()` function may now properly use _value_ and _context_ placeholders.
- Properly raise exceptions in `[value/candidate]_fstring_alias` for invalid `fstring` arguments.
- Added missing checks in `Mapper.__eq__()`.

### Removed
- The `misc.read_env_or_literal()` function has been replaced by `rics.misc.interpolate_environment_variables()`.

## [2.1.0] - 2023-02-11

### Changed
- Update log levels in `logs.basic_config()`.
- Move legend outside figure in `rics.performance.plot_run()`
- Only show the best overall candidates (per dataset) when using `mtimeit` / `run_multivariate_test()` by default.
- Add optional `ax` argument to `TimeFold.plot()`.

### Fixed
- Fixed behaviour of `TimeFold.plot()` in Jupyter notebooks. This function now returns an `Axes` object instead of a
  `Figure`, which prevents figures from being shown twice in notebooks. Technically a breaking changes, but will be 
  treated as a bugfix.
- Adjust figure height based on number of folds in `TimeFold.plot()`, unless `figsize` is given.
- Suppress fold log messages in `TimeFold.plot()`.

## [2.0.0] - 2022-11-30

### Added
- The `Mapper.copy` method.

### Changed
- Flatten/remove `rics.utility`; promote all modules to top-level members.
- `Mapper.apply` now require `context` with `InheritedKeysDict`-type overrides.

### Fixed
- Fixed exact value-candidate match short-circuiting in `HeuristicScore`.

### Removed
- All `rics.translation` modules. Use [id-translation](https://github.com/rsundqvist/id-translation/) instead.

## [1.0.1] - 2022-11-26

### Changed
- Deprecate `rics.translation`. Use [id-translation](https://github.com/rsundqvist/id-translation/) instead.

## [1.0.0] - 2022-11-26
### Added
- The `logs.disable_temporarily` function (returns a context manager).
- Permit creation of derived classes with `Translator.from_config`.
- Flesh out description of the `Translatable` type variable.
- Ability for the perftest CLI program to create and run dummy tests.
- Utility method `utility.pandas.TimeFold.iter`: Create temporal k-folds from a heterogeneous `DataFrame`.
- Make SqlFetcher engine creation more customizable.
  - Add `SqlFetcher.create_engine`, which my be overridden.
  - Add optional `engine_kwargs` init argument.

### Changed
- Change definition of `Mapper.context_sensitive_overrides`; now also `True` for blank overrides regardless of type.
- Discard useless (no-source) fetchers in `MultiFetcher`.
- The `SqlFetcher` class now always includes the engine information in log messages.
- The `utility.misc.tname`-method now also considers `__name__` before falling back to `__class__.__name__`.
- The `utility.configure_stuff`-method now also sets the pandas `float_format` option.
- Renamed perftest CLI program to `mtimeit` (was: `rics-perf`).
- Feature gate all CLI functionality behind the new `cli` extra.

### Fixed
- Properly handle empty whitelists in `SqlFetcher`. Used to treat empty whitelist as no whitelist.

## [0.17.0] - 2022-09-29
### Added
- Option to print classname for functions when using `misc.tname`.
- Property `Translator.sources`
- The `Translator.map_scores` method. May be used to fetch the raw name-to-source match score matrix.

### Changed
- Print less duplicate information in `Mapper.compute_scores` and `Mapper.apply`.
- Make `Mapper.compute_scores` and `Mapper.apply` respect the iteration order of its arguments when there are match conflicts.
- Improve messaging when translation is aborted due to mapping failure.

## [0.16.1] - 2022-09-23

### Changed
- Switch from `toml` to `tomli` for reading `Translator` config files.
- Improve documentation for troubleshooting mapping issues

### Fixed
- The `utility.logs.basic_config`-function now properly uses the `format` and `datefmt` arguments.

## [0.16.0] - 2022-09-12

### Changed
- Improved handling of NaN IDs. Move all NaN handling in `AbstractFetcher` to the `Translator`.
- Raise a `MappingError` for ambiguous name-to-source mapping.

### Fixed
- The `AbstractFetcher` no longer treats zero-length ID collections as a fetch-all instruction.
- Cast `float` to `int` when extracting IDs from a pandas `DataFrame` or `Series`.

## [0.15.3] - 2022-09-05

### Fixed
- Respect index order in `MatchScores.to_directional_mapping`.

## [0.15.2] - 2022-09-05

### Fixed
- Make sure `Mapper.compute_scores` score respects given value/candidate order.

## [0.15.1] - 2022-09-02

### Changed
- Added `duplicate_key_action` arg to `utility.dicts.reverse_dict`

### Fixed
- Duplicate derived names for candidates in for perftests.
- Improve handling for optional `Format` blocks (#52). Nested optional blocks are *not* supported.

## [0.15.0] - 2022-08-01

### Added
- Verbosity-flags to control high-volume mapping function invocation logging.
- Mapping primer page to the docs.
- Multiple improvements to the `Mapper` class through a new `mapping.support` module:
  - Improved logging capabilities.
  - Force respecting `cardinality` argument in `Mapper.apply` (fewer errors are raised).
  - Allow users to retrieve raw score matrices (`Mapper.compute_scores`).
  - Improved documentation and added new links is multiple places.
- Possibility to override select filtering logic; `SqlFetcher.selection_filter_type`.
- An optional `add_length_ratio_term` argument to `score_functions.modified_hamming`.
- The `utiltiy.collections.as_list` function for wrapping in/casting to list
- Support for translating an attribute of `translatable` in `Translator.translate`.
  - Names may be inherited from the parent (ie a pandas `Index` may inherit the name of the series)
- Cookbook recipes for translating dict keys and Pandas index types.
- Translation of `pandas.Index` types.
- The `translation.testing` module.
- Experimental and hacky implementation of translation for nested sequences.
- Entry point `rics-perf` for multivariate performance testing, taking candidates from `./candidates.py`
  and test case data from `./test_data.py`.

### Changed
- Rename `Translator.map_to_sources` -> `map`.
- Simplify `Translator.translate` signature.
  - Names must now be explicit names or None (use heuristics to filter names).
  - Simplify multiple docstrings.
- Permit `Translator` instances to be created with explicit fetch data. Translations will be generated based on the 
  inputs by using a `TestFetcher` instance. Functionality in this mode is limited.
- Performance testing figures updated; now shows best result as well.

### Removed
- An unnecessary restriction on runtime override functions in `Mapper`
- The `fetching.support.from_records` method. Fixes spurious exceptions from `PandasFetcher` (#99).
- Dunder `Mapper.__call__`.
- Expected runtime checks for perftests.

### Fixed
- An issue when using integers as explicit names to translate.
- It is now possible to use one name per element when translating sequences.
- Perftest argument `time_per_candidate` now used correctly.
- Filter out `NaN` values in `AbstractFetcher`.


## [0.14.0] - 2022-07-17

### Changed
- Added home page shortcuts.
- Rename 'default_translations' and 'default' arguments to 'default_fmt_placeholders' .

### Fixed
- Remove placeholder limitation on default translation format.
- Fixed issue when copying a `Translator` with translation and/or `Format` overrides.
- A number of docstring and under-the-hood fixes.

## [0.13.0] - 2022-07-10

Bump development status to `Development Status :: 3 - Alpha` on PyPi. 
Switched to the [PyData Sphinx theme](https://github.com/pydata/pydata-sphinx-theme) and enabled automatic summaries.

### Changed
- Name of `OfflineError` changed to `ConnectionStatusError`.
- Moved `Cardinality` to the `mapping` namespace.
- Move `utility.perf` up one level.
- Swapped generic `TypeVar` order for `IdType` and `SourceType` to match the name -> source -> ID hierarchy.

### Added
- Implement override functions in `Mapper.apply`.
  - Also: Partial implementation of override functions for name-to-source mapping in `Translator.translate`.
- Implement reverse translations. Added `reverse` argument to `Translator.translate` to translate from translations back to IDs.
- An option `maximal_untranslated_fraction` to raise an error if translation fails for too many IDs in `Translator.translate`.
- Make it possible to initialize `Fetcher`s from arbitrary packages in `Translator.from_config`.
- Make it possible configure `ScoreFunction`s, `FilterFunction`s and `AliasFunction`s from arbitrary modules .
  (still defaults to package functions).
- The `py.typed` marker (PEP-561 compliance).
- Additional `types`-modules for typehint imports.

### Fixed
- Numerous doc fixes.

## [0.12.2] - 2022-07-04

### Fixed
- Fixed chained alias functionality for `HeuristicScore`.

## [0.12.1] - 2022-07-04
Botched release.

## [0.12.0] - 2022-07-03

### Changed
- Changed `like_database_table` from score function to alias function.
- Thread safety: Change 'candidates' from init/property to `Mapper.apply` arg.
- Remove `store`/`restore` serialize argument. Default path is now None for `Translator.store`.

## [0.11.1] - 2022-07-02
Documentation and docstring fixes.

### Added
- A [TOML Configuration](https://rics.readthedocs.io/en/latest/translation-config-format.html) section to docs.

## [0.11.0] - 2022-07-01

### Added
- Convenience functions for (de)serializing `Translator` instances.

### Fixed
- Broken docs.

## [0.10.2] - 2022-07-01
Try to restore the translation API docs.

## [0.10.1] - 2022-06-30

### Fixed
- The `Translator` retrieving incorrect sources in offline mode.

## [0.10.0] - 2022-06-30
Refactor scoring functions.

### Added
- The `HeuristicScore` class, which enables filter-based short-circuiting and alias heuristics for score functions.

### Removed
- The `filter_functions.score_with_heuristics` function; replaced by the more general `HeuristicScore` class.

### Changed
- Make `translation.factory` module public.
- Rename `MappingScoreFunction` -> `ScoreFunction`.
- Add a third mandatory `context` parameter to all mapping functions. The `source` argument has been removed.

### Fixed
- Fix handling logging of duplicate source discovery in MultiFetcher.
- Allow empty fetching section in main config file when extra_fetchers are given.

## [0.9.0] - 2022-06-28

### Added
- Short-circuiting logic to `filter_functions.score_with_heuristics`.

### Fixed
- Some scoring stuff and related logging.

## [0.8.1] - 2022-06-28

### Fixed
- Fix unwanted case-sensitivity in `filter_functions.score_with_heuristics`.
- Allow user-defined cardinality in config files.
- Missing `Cardinality.parse(str)` case.

## [0.8.0] - 2022-06-28

### Added
- Support for fetching using multiple fetchers using the `MultiFetcher` class (#44).
- The `fetching.types` module.
- The `Fetcher` interface. The old `Fetcher` class in now called `AbstractFetcher`.
- The `action_level.ActionLevel` enum type.

### Changed
- Refactor score and filter functions (`mapping`-module) to increase flexibility and cover more use cases (#57, #58).

## [0.7.0] - 2022-06-21

### Added
- The `InheritedKeysDict` class.
- Integration of `Mapper` in the `Fetcher` for programmatic placeholder-mapping.
- Filtering logic for `Mapper`.
- The `plottting.pi_ticks`-function to plot an (X-)axis in terms of PI.
- Dvdrental testcase and docs running against a docker DB (not in CI)

### Changed
- More plotting functions.
- Improved dependency management. Added new dependency groups `translation` and `plotting` to be installed as extras.

## [0.6.0] - 2022-06-17
### Added
- Copy method for `Translator.copy(**overrides)`.

### Changed
- Switch from YAML to TOML for `Translator.config`.

## [0.5.0] - 2022-06-14
A large number of changes, bugfixes and stability improvements. Only the most important ones are listed here.

### Added
- Implement shared default translations (#31).
- Implement in-place translation for sequences (`list`, `pandas.Series`, `numpy.array`).
- Allow alternative use of translation format with an ID placeholder, even if the main doesn't include it.
- Add an option to run `Translator.store` with explicit data to cache.
- Implement alternative format for unknown IDs.
- Dict utility methods in `rics.utility.collections`.

### Changed
- SqlFetcher: Break out potentially expensive operations into overridable methods
- Replace suffix `_log_level` -> `_level` in `basic_config`

### Fixed
- Fix name extraction for `pandas.Series`

## [0.4.0] - 2022-03-24
### Added
- The `rics.utility.plotting` module.

## [0.3.2] - 2022-03-17
### Added
- The `Translator.fetch` function for retrieving IDs.

### Fixed
- Revert bad commit.
- Fix an issue in `PandasFetcher`.
- Some `SqlFetcher` warning messages.

## [0.3.1] - 2022-03-17
### Fixed
- Readme links.

## [0.3.0] - 2022-03-17
### Changed
- Update `get_local_or_remote` - remote root mandatory, default to cwd for local root.

### Added
- Make it possible to use predicates for `names` and `ignore_name` in `Translator.translate`.
- Add `Translator.map_to_sources` to get name-to-source mapping without translating data.

### Fixed
- Translation using formats which don't include the `id` placeholder.

## [0.2.0] - 2022-03-15
### Changed
- Update `Fetcher` return format from dict-of-lists to matrix (performance optimization).

### Added
- Database table discovery (gathers metadata like size and columns) for `SqlFetcher`.
- Add selection logic (used to always fetch everything) for `SqlFetcher`.
- Implement translations of `pandas.Series`.
- The `rics.utility.perf` package for multivariate (`data` x `functions`) performance testing.

### Fixed
- Fix fetching only required placeholders in `SqlFetcher`.

## [0.1.0] - 2022-03-12
First release on PyPI!

### Added
- The `rics.utility` package for various common operations.
- The `rics.translation` package suite for translating IDs into human-readable labels.
- The `rics.mapping` package for linking elements in multiple directions.
- The `rics.cardinality` package; enum types for `1:1`, `1:N`, `N:1`, and `M:N`.

[Unreleased]: https://github.com/rsundqvist/rics/compare/v5.0.0...HEAD
[5.0.0]: https://github.com/rsundqvist/rics/compare/v4.1.1...v5.0.0
[4.1.1]: https://github.com/rsundqvist/rics/compare/v4.1.0...v4.1.1
[4.1.0]: https://github.com/rsundqvist/rics/compare/v4.0.1...v4.1.0
[4.0.1]: https://github.com/rsundqvist/rics/compare/v4.0.0...v4.0.1
[4.0.0]: https://github.com/rsundqvist/rics/compare/v3.3.0...v4.0.0
[3.3.0]: https://github.com/rsundqvist/rics/compare/v3.2.0...v3.3.0
[3.2.0]: https://github.com/rsundqvist/rics/compare/v3.1.0...v3.2.0
[3.1.0]: https://github.com/rsundqvist/rics/compare/v3.0.1...v3.1.0
[3.0.1]: https://github.com/rsundqvist/rics/compare/v3.0.0...v3.0.1
[3.0.0]: https://github.com/rsundqvist/rics/compare/v2.1.0...v3.0.0
[2.1.0]: https://github.com/rsundqvist/rics/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/rsundqvist/rics/compare/v1.0.1...v2.0.0
[1.0.1]: https://github.com/rsundqvist/rics/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/rsundqvist/rics/compare/v0.17.0...v1.0.0
[0.17.0]: https://github.com/rsundqvist/rics/compare/v0.16.1...v0.17.0
[0.16.1]: https://github.com/rsundqvist/rics/compare/v0.16.0...v0.16.1
[0.16.0]: https://github.com/rsundqvist/rics/compare/v0.15.3...v0.16.0
[0.15.3]: https://github.com/rsundqvist/rics/compare/v0.15.2...v0.15.3
[0.15.2]: https://github.com/rsundqvist/rics/compare/v0.15.1...v0.15.2
[0.15.1]: https://github.com/rsundqvist/rics/compare/v0.15.0...v0.15.1
[0.15.0]: https://github.com/rsundqvist/rics/compare/v0.14.0...v0.15.0
[0.14.0]: https://github.com/rsundqvist/rics/compare/v0.13.0...v0.14.0
[0.13.0]: https://github.com/rsundqvist/rics/compare/v0.12.2...v0.13.0
[0.12.2]: https://github.com/rsundqvist/rics/compare/v0.12.1...v0.12.2
[0.12.1]: https://github.com/rsundqvist/rics/compare/v0.12.0...v0.12.1
[0.12.0]: https://github.com/rsundqvist/rics/compare/v0.11.1...v0.12.0
[0.11.1]: https://github.com/rsundqvist/rics/compare/v0.11.0...v0.11.1
[0.11.0]: https://github.com/rsundqvist/rics/compare/v0.10.2...v0.11.0
[0.10.2]: https://github.com/rsundqvist/rics/compare/v0.10.1...v0.10.2
[0.10.1]: https://github.com/rsundqvist/rics/compare/v0.10.0...v0.10.1
[0.10.0]: https://github.com/rsundqvist/rics/compare/v0.9.0...v0.10.0
[0.9.0]: https://github.com/rsundqvist/rics/compare/v0.8.1...v0.9.0
[0.8.1]: https://github.com/rsundqvist/rics/compare/v0.8.0...v0.8.1
[0.8.0]: https://github.com/rsundqvist/rics/compare/v0.7.0...v0.8.0
[0.7.0]: https://github.com/rsundqvist/rics/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/rsundqvist/rics/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/rsundqvist/rics/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/rsundqvist/rics/compare/v0.3.2...v0.4.0
[0.3.2]: https://github.com/rsundqvist/rics/compare/v0.3.1...v0.3.2
[0.3.1]: https://github.com/rsundqvist/rics/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/rsundqvist/rics/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/rsundqvist/rics/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/rsundqvist/rics/compare/releases/tag/v0.1.0
