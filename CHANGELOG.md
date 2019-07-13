# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.3] - 2019-07-13
## Changed
- Fixed issue #2, windows version did not work because file paths had mixed
slashes and backslashes. File path must be normalized with os.path.normpath()

## [1.0.2] - 2018-10-25
## Added
- Enforced Python version 2

## [1.0.1] - 2018-03-12
### Added
- Deduplication mechanism with `--nodedup` flag.
- A test for deduplication
- CHANGELOG.md file
### Changed
- Simplified running tests
- Better versioning

## [1.0.0] - 2018-03-07
### Added
- Initial revision

