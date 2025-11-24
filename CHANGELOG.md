# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project structure
- Lexer module using Python's tokenize
- Parser module using Python's ast
- Semantic analysis module (partial implementation)
- Code generation module
- Optimizer module (placeholder)
- Minifier module (fully functional)
- CLI interface with all options
- Comprehensive test suite
- Documentation (README, QUICKSTART, IMPLEMENTATION)

### Implemented
- ✅ Code minification (removes docstrings and comments)
- ✅ Single file processing
- ✅ Recursive directory processing
- ✅ Dry-run mode
- ✅ CLI with all options from specification

### Not Yet Implemented
- ⚠️ Tree-shaking optimization
- ⚠️ Call graph analysis
- ⚠️ Module renaming with __ma suffix
- ⚠️ Cross-module optimization
- ⚠️ Semantic analysis (partial)

## [0.1.0] - 2025-11-23

### Added
- Initial release
- Basic minification functionality
- Project structure following specification
