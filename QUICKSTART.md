# Quickstart Guide

## Installation

1. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Linux/Mac
# or
venv\Scripts\activate  # On Windows
```

2. Install the package in development mode:
```bash
pip install -e ".[dev]"
```

## Usage Examples

### 1. Minify a single file (preview with --dry-run)

```bash
minimal-app examples/mini_ds.py --dry-run -v
```

### 2. Minify a single file and save to output

```bash
minimal-app examples/mini_ds.py -o examples/mini_ds.min.py
```

### 3. Minify all Python files in a directory recursively

```bash
minimal-app examples/ -r -o build/ -v
```

### 4. Keep docstrings while minifying

```bash
minimal-app examples/app.py --keep-docstrings --dry-run
```

### 5. Tree-shaking with entrypoint (not yet implemented)

```bash
minimal-app examples/ -r -o build/ --entrypoint app:handler
```

This will show a message that tree-shaking is not yet implemented.

## Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=minimal_app --cov-report=term-missing
```

## Linting

```bash
# Check code style
ruff check src tests

# Auto-fix issues
ruff check src tests --fix
```

## What's Implemented

✅ **Code minification** - Removes docstrings and comments using Python's AST
✅ **CLI interface** - Full command-line interface with all options
✅ **Single file processing** - Minify individual Python files
✅ **Directory processing** - Recursively process entire directories
✅ **Dry-run mode** - Preview changes without writing files
✅ **Keep options** - Option to preserve docstrings
✅ **Tests** - Comprehensive test suite with 15 tests

## What's Not Implemented (Placeholders)

⚠️ **Tree-shaking** - Semantic analysis and dead code elimination
⚠️ **Call graph analysis** - Building dependency graphs from entrypoints
⚠️ **Module renaming** - Adding `__ma` suffix to optimized modules
⚠️ **Cross-module optimization** - Optimizing across module boundaries

## Example Output

**Before minification:**
```python
"""Example: mini_ds.py - A tiny DataFrame-like class."""

class MyDataFrame:
    """Tiny demo DataFrame-like class."""
    
    def __init__(self, data: list[int]) -> None:
        self.data: list[int] = data
    
    def head(self, n: int = 5) -> "MyDataFrame":
        """Return first n elements."""
        return MyDataFrame(self.data[:n])
```

**After minification:**
```python
class MyDataFrame:

    def __init__(self, data: list[int]) -> None:
        self.data: list[int] = data

    def head(self, n: int=5) -> 'MyDataFrame':
        return MyDataFrame(self.data[:n])
```

All docstrings and comments are removed while preserving the code structure and functionality!
