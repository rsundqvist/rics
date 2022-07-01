# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [Unreleased]

### Added
- Convenience functions for (de)serializing `Translator` instances.

### Fixed
- Broken docs.

## [0.10.2] - 2022-07-01
Try to restore the translation API docs.

## [0.10.1] - 2022-06-30

### Fixed
- The `Translator` retrieving incorrect sources in offline mode

## [0.10.0] - 2022-06-30
Refactor scoring functions.

### Added
- The `HeuristicScore` class, which enables filter-based short-circuiting and alias heuristics for score functions.

### Removed
- The `filter_functions.score_with_heuristics` function; replaced by the more general `HeuristicScore` class.

### Changed
- Make `translation.factory` module public
- Rename `MappingScoreFunction` -> `ScoreFunction`
- Add a third mandatory `context` parameter to all mapping functions. The `source` argument has been removed.

### Fixed
- Fix handling logging of duplicate source discovery in MultiFetcher
- Allow empty fetching section in main config file when extra_fetchers are given

## [0.9.0] - 2022-06-28

### Added
- Short-circuiting logic to `filter_functions.score_with_heuristics`

### Fixed
- Some scoring stuff and related logging.

## [0.8.1] - 2022-06-28

### Fixed
- Fix unwanted case-sensitivity in `filter_functions.score_with_heuristics`
- Allow user-defined cardinality in config files
- Missing `Cardinality.parse(str)` case

## [0.8.0] - 2022-06-28

### Added
- Support for fetching using multiple fetchers using the `MultiFetcher` class (#44)
- The `fetching.types` module.
- The `Fetcher` interface. The old `Fetcher` class in now called `AbstractFetcher`.
- The `action_level.ActionLevel` enum type.

### Changed
- Refactor score and filter functions (`mapping`-module) to increase flexibility and cover more use cases (#57, #58).

## [0.7.0] - 2022-06-21

### Added
- The `InheritedKeysDict` class.
- Integration of `Mapper` in the `Fetcher` for programmatic placeholder-mapping.
- Filtering logic for `Mapper`
- The `plottting.pi_ticks`-function to plot an (X-)axis in terms of PI.
- Dvdrental testcase and docs running against a docker DB (not in CI)

### Changed
- More plotting functions
- Improved dependency management. Added new dependency groups `translation` and `plotting` to be installed as extras

## [0.6.0] - 2022-06-17
### Added
- Copy method for `Translator.copy(**overrides)`.

### Changed
- Switch from YAML to TOML for `Translator.config`.

## [0.5.0] - 2022-06-14
A large number of changes, bugfixes and stability improvements. Only the most important ones are listed here.

### Added
- Implement shared default translations (#31)
- Implement in-place translation for sequences (`list`, `pandas.Series`, `numpy.array`)
- Allow alternative use of translation format with an ID placeholder, even if the main doesn't include it
- Add an option to run `Translator.store` with explicit data to cache
- Implement alternative format for unknown IDs

### Changed
- SqlFetcher: Break out potentially expensive operations into overridable methods
- Replace suffix `_log_level` -> `_level` in `basic_config`

### Fixed
- Fix name extraction for `pandas.Series`

### Added
- Dict utility methods in `rics.utility.collections`

## [0.4.0] - 2022-03-24
### Added
- The `rics.utility.plotting` module

## [0.3.2] - 2022-03-17
### Added
- The `Translator.fetch` function for retrieving IDs

### Fixed
- Revert bad commit
- Fix an issue in `PandasFetcher`
- Some `SqlFetcher` warning messages

## [0.3.1] - 2022-03-17
### Fixed
- Readme links.

## [0.3.0] - 2022-03-17
### Changed
- Update `get_local_or_remote` - remote root mandatory, default to cwd for local root

### Added
- Make it possible to use predicates for `names` and `ignore_name` in `Translator.translate`
- Add `Translator.map_to_sources` to get name-to-source mapping without translating data

### Fixed
- Translation using formats which don't include the `id` placeholder

## [0.2.0] - 2022-03-15
### Changed
- Update `Fetcher` return format from dict-of-lists to matrix (performance optimization)

### Added
- Database table discovery (gathers metadata like size and columns) for `SqlFetcher`
- Add selection logic (used to always fetch everything) for `SqlFetcher`
- Implement translations of `pandas.Series`
- The `rics.utility.perf` package for multivariate (`data` x `functions`) performance testing

### Fixed
- Fix fetching only required placeholders in `SqlFetcher`

## [0.1.0] - 2022-03-12
First release on PyPI!

### Added
- The `rics.utility` package for various common operations
- The `rics.translation` package suite for translating IDs into human-readable labels
- The `rics.mapping` package for linking elements in multiple directions
- The `rics.cardinality` package; enum types for `1:1`, `1:N`, `N:1`, and `M:N`

[Unreleased]: https://github.com/rsundqvist/rics/compare/v0.10.2...HEAD
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
