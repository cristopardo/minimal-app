# minimal-app

minimal-app is a compiler-inspired optimizer for statically typed Python. It runs lexical, syntactic and semantic analysis on your codebase, builds a cross-module call graph rooted at a single entrypoint, and performs aggressive tree-shaking to strip unused imports, functions, classes, methods, comments and docstrings — producing tiny, deployment-ready bundles ideal for AWS Lambda, serverless and container builds.

---

## Features

- **Code minification**  
  Removes comments, docstrings and unnecessary whitespace while keeping valid Python.

- **Semantic tree-shaking (single entrypoint)**  
  Builds a call graph from a single entrypoint (e.g. `app:handler`) and drops unreachable imports, functions, classes and methods across modules.

- **Closed-world optimization**  
  Treats your project and its (statically importable) libraries as a closed world, optimizing across module boundaries.

- **Canonical bundling & renaming**  
  Writes an optimized bundle that preserves your folder structure but renames modules/packages and the entrypoint using a consistent suffix (`__ma`).

- **Serverless-oriented**  
  Generates minimal bundles for AWS Lambda and similar FaaS/container deployments.

- **Modern toolchain**  
  Uses `ruff` for linting and `pytest` for unit tests.

- **PyPI-ready CLI**  
  Distributed as an installable CLI tool from PyPI, with a modern `pyproject.toml`-based setup. 
---

## Assumptions & Limitations

minimal-app deliberately targets a restricted, compiler-friendly subset of Python:

- **Typed Python only**  
  The tool assumes **complete and correct type hints** for functions, methods, parameters and return types. Type information is used to resolve calls and build the call graph.

- **Single entrypoint**  
  Tree-shaking is rooted at **one entrypoint** provided as `module:function`, e.g. `app:handler`.  
  Only code reachable from that entrypoint is kept. Multiple entrypoints are not supported.

- **Static imports**  
  - No `from x import *`.  
  - No dynamic imports such as `__import__`, `importlib.import_module` with variable names, etc.

- **No dynamic reflection for behavior**  
  - No `eval`/`exec`-driven code paths.  
  - No heavy use of `getattr/setattr` to select methods by runtime strings.  
  - No monkey-patching of classes or modules at runtime.

- **Closed world**  
  All relevant source files (your app and any local “library-like” modules you want to optimize) are available as `.py` files under the analyzed directory.

If your code violates these assumptions, minimal-app may fall back to conservative behavior (keeping more code) or may not work correctly yet.

---

## Installation

(Once published to PyPI:)

```bash
pip install minimal-app
```

From source (editable install with dev tools):

```bash
git clone https://github.com/<your-user>/minimal-app.git
cd minimal-app
pip install -e ".[dev]"
```

The `dev` extra is expected to include at least:

- `ruff` – linter  
- `pytest` – test runner  

---

## Quickstart (CLI)

The CLI entry point is `minimal-app` and accepts either a single `.py` file or a directory.

### Minify a single file (no entrypoint)

Pure lexical/structural minification — **no call-graph analysis**:

```bash
minimal-app app.py -o app.min.py
```

This will:

- Parse `app.py`.  
- Remove comments, docstrings and unnecessary whitespace.  
- Preserve the behavior of the file.  

### Tree-shake and bundle a project from a single entrypoint

To run semantic optimization (tree-shaking + renaming), you must specify a **single entrypoint**:

```bash
minimal-app src/   -r   -o build/   --entrypoint app:handler
```

This will:

- Walk `src/` recursively.  
- Build a call graph starting from `app.handler`.  
- Remove unreachable imports, functions, classes and methods.  
- Write an optimized, consistently renamed bundle into `build/`.  

You can then package `build/` for AWS Lambda, containers, etc.

---

## Canonical bundling & renaming (`__ma` suffix)

When running with an entrypoint, minimal-app produces a canonical, renamed bundle that **preserves the original folder structure** but appends a suffix to each package and module:

- Every Python package or module name gets the suffix:

  `__ma`  (double underscore + `ma`)

  For example:

  - `src/app.py` → `build/app__ma.py`  
  - `src/mini_ds.py` → `build/mini_ds__ma.py`  
  - `src/myapp/__init__.py` → `build/myapp__ma/__init__.py`  
  - `src/myapp/utils/io.py` → `build/myapp__ma/utils__ma/io__ma.py`  

- The **original entrypoint** (e.g. `app:handler`) is remapped to:

  `app__ma:handler__ma`

  which means a final AWS Lambda handler like:

  ```text
  app__ma.handler__ma
  ```

- All **imports inside the bundle** are rewritten to reference the new names:

  ```python
  # original
  from mini_ds import MyDataFrame

  # bundled
  from mini_ds__ma import MyDataFrame
  ```

  ```python
  # original
  from myapp.utils.io import save_json

  # bundled
  from myapp__ma.utils__ma.io__ma import save_json
  ```

Original paths and folder names remain recognizable (with the `__ma` suffix), while the optimized bundle lives in a separate output tree (e.g. `build/`), avoiding collisions with the source code.

In future versions, the suffix may be configurable (e.g. via `--suffix`); for now it is fixed as `__ma`.

---

## Small Example

### Input project

```text
src/
├─ mini_ds.py
└─ app.py
```

**`src/mini_ds.py`**

```python
class MyDataFrame:
    'Tiny demo DataFrame-like class.'

    def __init__(self, data: list[int]) -> None:
        self.data: list[int] = data

    def head(self, n: int = 5) -> "MyDataFrame":
        'Return first n elements.'
        return MyDataFrame(self.data[:n])

    def tail(self, n: int = 5) -> "MyDataFrame":
        'Return last n elements.'
        return MyDataFrame(self.data[-n:])

    def sum(self) -> int:
        'Return the sum of all elements.'
        return sum(self.data)

    def unused(self) -> None:
        # This method is never called.
        print("I am dead code")
```

**`src/app.py`**

```python
from mini_ds import MyDataFrame


def handler(event: dict, context: object) -> dict:
    'Lambda-style entrypoint.'
    df = MyDataFrame([1, 2, 3, 4, 5])
    head = df.head(3)
    return {'sum': head.sum()}
```

In this example:

- The entrypoint passed to minimal-app is `app:handler`.  
- `MyDataFrame.tail` and `MyDataFrame.unused` are never used.  
- Comments and docstrings are not needed at runtime.  

### Running minimal-app

```bash
minimal-app src/   -r   -o build/   --entrypoint app:handler
```

### Output (with `__ma` suffixes)

```text
build/
├─ app__ma.py
└─ mini_ds__ma.py
```

**`build/mini_ds__ma.py`**

```python
class MyDataFrame:
    def __init__(self, data: list[int]) -> None:
        self.data = data

    def head(self, n: int = 5) -> "MyDataFrame":
        return MyDataFrame(self.data[:n])

    def sum(self) -> int:
        return sum(self.data)
```

**`build/app__ma.py`**

```python
from mini_ds__ma import MyDataFrame


def handler__ma(event: dict, context: object) -> dict:
    df = MyDataFrame([1, 2, 3, 4, 5])
    head = df.head(3)
    return {'sum': head.sum()}
```

The final AWS Lambda handler would then be:

```text
app__ma.handler__ma
```

Comments and docstrings are removed, unused methods (`tail`, `unused`) are dropped, and module names and imports are consistently suffixed with `__ma`.

---

## CLI Usage & Options

> Note: names may evolve; this is the intended interface.

```text
minimal-app [OPTIONS] PATH

Arguments:
  PATH                       File or directory to optimize.

Options:
  -o, --output PATH          Output file or directory (default: overwrite in-place).
  --entrypoint MOD:FUNC      Single entrypoint for reachability analysis (required for tree-shaking).
  --keep-comments            Keep line comments (docstrings are still removed).
  --keep-docstrings          Keep docstrings (by default they are removed).
  --dry-run                  Show a summary of planned changes without writing files.
  -v, --verbose              Increase log verbosity (can be used multiple times).
  --version                  Show minimal-app version.
  -h, --help                 Show this message and exit.
```

- If `--entrypoint` is **omitted**, minimal-app performs **lexical/structural minification only** (no tree-shaking, no renaming).  
- If `--entrypoint` is provided, there must be exactly **one** entrypoint.  

---

## Configuration

You can configure default behavior via `pyproject.toml`:

```toml
[tool.minimal-app]
recursive = true
keep-comments = false
keep-docstrings = false
entrypoint = "app:handler"
```

CLI flags always override configuration values.

---

## Project Structure

A typical layout for this repository:

```text
minimal-app/
├─ src/
│  └─ minimal_app/
│     ├─ __init__.py
│     ├─ cli.py
│     ├─ lexer.py
│     ├─ parser.py
│     ├─ semantic.py
│     ├─ optimizer.py
│     └─ codegen.py
├─ tests/
│  ├─ test_cli.py
│  ├─ test_optimizer.py
│  └─ test_integration.py
├─ pyproject.toml
├─ README.md
├─ LICENSE
└─ CHANGELOG.md
```

---

## Development

Clone the repo and install dev dependencies:

```bash
git clone https://github.com/<your-user>/minimal-app.git
cd minimal-app
pip install -e ".[dev]"
```

### Running tests

```bash
pytest
```

With coverage:

```bash
pytest --cov=minimal_app --cov-report=term-missing
```

### Linting

```bash
ruff check src tests
```

Optionally, auto-fix:

```bash
ruff check src tests --fix
```

You can integrate `ruff` and `pytest` with `pre-commit`:

```bash
pre-commit install
pre-commit run --all-files
```

---

## License

Specify your license here (e.g. MIT, Apache-2.0).
