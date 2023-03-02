# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [Unreleased]

### Added
- The `score_functions.disabled()` function, used to force a `Mapper` to work in override-only mode.

### Changed
- Add `n_splits` argument to `TimeFold` (scikit-learn compatibility).

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

[Unreleased]: https://github.com/rsundqvist/rics/compare/v2.1.0...HEAD
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
