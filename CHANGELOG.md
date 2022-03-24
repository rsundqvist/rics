# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [Unreleased]
### Changed
- Replace suffix `_log_level -> `_level` in `basic_config`

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
- Fix an issue in PandasFetcher
- Some SqlFetcher warning messages

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
- Update Fetcher return format from dict-of-lists to matrix (performance optimization)

### Added
- Database table discovery (gathers metadata like size and columns) for SqlFetcher
- Add selection logic (used to always fetch everything) for SqlFetcher
- Implement translations of `pandas.Series`
- The `rics.utility.perf` package for multivariate (`data` x `functions`) performance testing

### Fixed
- Fix fetching only required placeholders in SqlFetcher

## [0.1.0] - 2022-03-12
First release on PyPI!

### Added
- The `rics.utility` package for various common operations
- The `rics.translation` package suite for translating IDs into human-readable labels
- The `rics.mapping` package for linking elements in multiple directions
- The `rics.cardinality` package; enum types for `1:1`, `1:N`, `N:1`, and `M:N`

[Unreleased]: https://github.com/rsundqvist/rics/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/rsundqvist/rics/compare/v0.3.2...v0.4.0
[0.3.2]: https://github.com/rsundqvist/rics/compare/v0.3.1...v0.3.2
[0.3.1]: https://github.com/rsundqvist/rics/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/rsundqvist/rics/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/rsundqvist/rics/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/rsundqvist/rics/compare/releases/tag/v0.1.0
