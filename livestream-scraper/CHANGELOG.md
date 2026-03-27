# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-03-27

### Added
- Initial release of LiveStream Phone Extractor
- Playwright-based browser automation
- Multi-format phone number pattern matching
- Real-time extraction with CSV/JSON/TXT output
- Configurable via YAML files
- Headless and headed browser modes
- Automatic scrolling for dynamic content loading
- Progress reporting and statistics
- Graceful shutdown with data preservation
- Comprehensive documentation
- Test suite with pytest
- MIT license with legal notices

### Features
- Extract Chinese mobile phone numbers from live streams
- Support for multiple formats (13800138000, 138-0013-8000, +86 138...)
- Deduplication with occurrence counting
- Context preservation (surrounding text)
- Backup functionality for long-running sessions
- Command-line interface with argument parsing
- Extensible architecture for custom extractors

### Documentation
- Installation guide
- Configuration reference
- API documentation
- Development guide
- Legal and ethical guidelines
- Contributing guidelines

## [Unreleased]

### Planned
- Webhook notifications for real-time alerts
- Docker containerization
- Support for additional live stream platforms
- Machine learning-based pattern detection
- Database integration (PostgreSQL, MongoDB)
- REST API for remote control
- Web dashboard for monitoring
- Multi-threading support
- Proxy rotation support

---

## Release Notes Template

```
## [X.Y.Z] - YYYY-MM-DD

### Added
- New features

### Changed
- Changes in existing functionality

### Deprecated
- Soon-to-be removed features

### Removed
- Now removed features

### Fixed
- Bug fixes

### Security
- Security improvements
```
