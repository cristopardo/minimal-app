"""Tree-shaking optimizer for minimal-app.

Implements:
- Project discovery (modules under a root path)
- Call graph construction from a single entrypoint
- Reachability analysis (which symbols are "alive")
- AST pruning (functions, classes, methods, docstrings)
- Canonical bundling with __ma suffix and import rewriting
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Set, Tuple

from .parser import parse_file  # parses a Path -> ast.Module :contentReference[oaicite:2]{index=2}
from .semantic import build_call_graph, compute_reachable_symbols  # :contentReference[oaicite:3]{index=3}
from .codegen import write_module  # writes an AST to disk :contentReference[oaicite:4]{index=4}

SUFFIX = "__ma"


@dataclass
class ModuleInfo:
    """In-memory representation of a module in the project."""

    name: str        # dotted module name, e.g. "app" or "myapp.utils.io"
    path: Path       # original filesystem path
    tree: ast.Module
    is_package: bool # True if this is a package (__init__.py)


# --------------------------------------------------------------------------- utils


def _module_name_from_path(path: Path, root: Path) -> Tuple[str, bool]:
    """Compute dotted module name from path relative to root.

    Examples
    --------
    root = /project/src
    path = /project/src/app.py              -> ("app", False)
    path = /project/src/myapp/__init__.py   -> ("myapp", True)
    path = /project/src/myapp/utils/io.py   -> ("myapp.utils.io", False)
    """
    rel = path.relative_to(root)
    parts = list(rel.parts)
    is_package = False

    if parts[-1].endswith(".py"):
        parts[-1] = parts[-1][:-3]

    if parts[-1] == "__init__":
        is_package = True
        parts = parts[:-1]

    module_name = ".".join(parts) if parts else "__main__"
    return module_name, is_package


def _discover_modules(input_path: Path, recursive: bool) -> Tuple[Path, Dict[str, ModuleInfo]]:
    """Discover all Python modules under input_path.

    Returns
    -------
    root: Path
        Root directory used for module naming and for computing output paths.
    modules: Dict[str, ModuleInfo]
        Mapping dotted module name -> ModuleInfo
    """
    if input_path.is_file():
        root = input_path.parent.resolve()
        files = [input_path.resolve()]
    else:
        root = input_path.resolve()
        pattern = "**/*.py" if recursive else "*.py"
        files = sorted(root.glob(pattern))

    modules: Dict[str, ModuleInfo] = {}

    for path in files:
        if any(part.startswith(".") or part == "__pycache__" for part in path.parts):
            continue

        module_name, is_package = _module_name_from_path(path, root)
        tree = parse_file(path)
        modules[module_name] = ModuleInfo(
            name=module_name,
            path=path,
            tree=tree,
            is_package=is_package,
        )

    return root, modules


def _suffix_module_name(module_name: str) -> str:
    """Add SUFFIX to each component of a dotted module name.

    Examples
    --------
    "app"               -> "app__ma"
    "mini_ds"           -> "mini_ds__ma"
    "myapp.utils.io"    -> "myapp__ma.utils__ma.io__ma"
    """
    parts = module_name.split(".")
    return ".".join(part + SUFFIX for part in parts)


def _output_path_for_module(
    new_module_name: str,
    out_root: Path,
    is_package: bool,
) -> Path:
    """Compute output path for a module with the suffixed name."""
    parts = new_module_name.split(".")

    if is_package:
        # e.g. myapp__ma -> out_root/myapp__ma/__init__.py
        return out_root.joinpath(*parts, "__init__.py")
    else:
        # e.g. myapp__ma.utils__ma.io__ma -> out_root/myapp__ma/utils__ma/io__ma.py
        if len(parts) == 1:
            return out_root / f"{parts[0]}.py"
        return out_root.joinpath(*parts[:-1], f"{parts[-1]}.py")


# ---------------------------------------------------------------------- AST passes


class PruneTransformer(ast.NodeTransformer):
    """Remove unused functions, classes, methods and optionally docstrings."""

    def __init__(
        self,
        module_name: str,
        reachable_symbols: Set[str],
        keep_docstrings: bool,
        entry_function: str | None,
    ) -> None:
        self.module_name = module_name
        self.reachable_symbols = reachable_symbols
        self.keep_docstrings = keep_docstrings
        self.entry_function = entry_function
        self.current_class: str | None = None

    # --------------------------- helpers

    def _symbol_name(self, name: str) -> str:
        if self.current_class:
            return f"{self.module_name}:{self.current_class}.{name}"
        return f"{self.module_name}:{name}"

    def _class_symbol(self, class_name: str) -> str:
        return f"{self.module_name}:{class_name}"

    # ------------------------- visitors

    def visit_Module(self, node: ast.Module) -> ast.Module:
        # Remove module docstring if requested
        if not self.keep_docstrings and node.body:
            first = node.body[0]
            if (
                isinstance(first, ast.Expr)
                and isinstance(first.value, ast.Constant)
                and isinstance(first.value.value, str)
            ):
                node.body = node.body[1:] or [ast.Pass()]

        self.generic_visit(node)
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST | None:
        original_name = node.name
        fqname = self._symbol_name(original_name)

        keep = fqname in self.reachable_symbols

        # Always keep entrypoint function in its module
        if (not self.current_class) and self.entry_function == original_name:
            keep = True

        # For methods: keep __init__ if class is reachable
        if self.current_class and original_name == "__init__":
            class_sym = self._class_symbol(self.current_class)
            if class_sym in self.reachable_symbols:
                keep = True

        if not keep:
            return None

        # Rename entrypoint function with suffix
        if (not self.current_class) and self.entry_function == original_name:
            node.name = original_name + SUFFIX

        # Remove docstring if requested
        if not self.keep_docstrings and node.body:
            first = node.body[0]
            if (
                isinstance(first, ast.Expr)
                and isinstance(first.value, ast.Constant)
                and isinstance(first.value.value, str)
            ):
                node.body = node.body[1:]

        if not node.body:
            node.body = [ast.Pass()]

        self.generic_visit(node)
        return node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AST | None:
        # Same logic as for FunctionDef
        return self.visit_FunctionDef(node)  # type: ignore[arg-type]

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.AST | None:
        class_name = node.name
        class_sym = self._class_symbol(class_name)

        # First, prune methods inside the class
        prev_class = self.current_class
        self.current_class = class_name
        self.generic_visit(node)
        self.current_class = prev_class

        # Remove class docstring if requested
        if not self.keep_docstrings and node.body:
            first = node.body[0]
            if (
                isinstance(first, ast.Expr)
                and isinstance(first.value, ast.Constant)
                and isinstance(first.value.value, str)
            ):
                node.body = node.body[1:]

        # Decide whether to keep the class
        has_methods = any(
            isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef))
            for stmt in node.body
        )

        # If the class itself is reachable OR any method remains, we keep it
        if class_sym not in self.reachable_symbols and not has_methods:
            return None

        if not node.body:
            node.body = [ast.Pass()]

        return node


class ImportRewriter(ast.NodeTransformer):
    """Rewrite import targets to use suffixed module names."""

    def __init__(self, module_renames: Dict[str, str]) -> None:
        self.module_renames = module_renames

    def visit_Import(self, node: ast.Import) -> ast.AST:
        for alias in node.names:
            # alias.name is a full module path, e.g. "myapp.utils.io"
            if alias.name in self.module_renames:
                alias.name = self.module_renames[alias.name]
        return self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> ast.AST:
        if node.module and node.module in self.module_renames:
            node.module = self.module_renames[node.module]
        return self.generic_visit(node)


# --------------------------------------------------------------------------- main


def optimize_project(
    input_path: Path,
    output_path: Path | None,
    entrypoint: str,
    recursive: bool,
    keep_comments: bool,   # kept for API compatibility; no effect with AST
    keep_docstrings: bool,
    dry_run: bool,
    verbose: int,
) -> None:
    """
    Optimize a project with tree-shaking from a single entrypoint.

    Steps:
    - Discover modules and parse them into ASTs.
    - Build a call graph starting from the entrypoint.
    - Compute reachable symbols.
    - Prune unused functions/classes/methods.
    - Rewrite imports and module names with __ma suffix.
    - Write the resulting bundle to the output directory.
    """
    if ":" not in entrypoint:
        raise ValueError(
            f"Invalid entrypoint format: '{entrypoint}'. Expected 'module:function'."
        )

    entry_module, entry_func = entrypoint.split(":", 1)

    # 1) Descubrimos y parseamos todos los módulos
    root, modules = _discover_modules(input_path, recursive)

    if verbose > 0:
        print(f"[minimal-app] Discovered {len(modules)} module(s) under {root}")

    if entry_module not in modules:
        raise ValueError(
            f"Entrypoint module '{entry_module}' not found under {root}. "
            f"Available modules: {', '.join(sorted(modules))}"
        )

    # 2) Construimos el call graph
    modules_ast = {name: mi.tree for name, mi in modules.items()}
    cg = build_call_graph(modules_ast, entrypoint)

    # 3) Símbolos alcanzables desde el entrypoint
    reachable_symbols = compute_reachable_symbols(cg)

    if verbose > 0:
        print(f"[minimal-app] Reachable symbols: {len(reachable_symbols)}")

    # 4) Renombre canónico de módulos con __ma
    module_renames: Dict[str, str] = {
        name: _suffix_module_name(name) for name in modules.keys()
    }

    # 5) Determinar directorio de salida
    out_root = (output_path or root).resolve()
    if not dry_run:
        out_root.mkdir(parents=True, exist_ok=True)

    if verbose > 0:
        print(f"[minimal-app] Writing optimized bundle to: {out_root}")

    # 6) Para cada módulo, podar AST, reescribir imports y escribir archivo
    for mod_name, mi in modules.items():
        is_entry = (mod_name == entry_module)
        new_name = module_renames[mod_name]

        if verbose > 1:
            print(f"  - Optimizing module {mod_name} -> {new_name}")

        # Podado semántico
        pruner = PruneTransformer(
            module_name=mod_name,
            reachable_symbols=reachable_symbols,
            keep_docstrings=keep_docstrings,
            entry_function=entry_func if is_entry else None,
        )
        new_tree = pruner.visit(ast.fix_missing_locations(mi.tree))
        ast.fix_missing_locations(new_tree)

        # Reescritura de imports hacia módulos con sufijo __ma
        rewriter = ImportRewriter(module_renames)
        new_tree = rewriter.visit(new_tree)
        ast.fix_missing_locations(new_tree)

        # Ruta de salida para el módulo renombrado
        out_path = _output_path_for_module(new_name, out_root, mi.is_package)

        if dry_run:
            print(f"[dry-run] Would write: {mod_name} -> {out_path}")
            if verbose > 2:
                # Mostrar el código resultante (opcional)
                code_preview = ast.unparse(new_tree)
                print("---------")
                print(code_preview)
                print("---------")
        else:
            write_module(
                new_tree,
                output_path=out_path,
                module_name=mod_name,
                add_suffix=False,  # ya renombramos en el AST
            )

    if verbose > 0:
        print("[minimal-app] Optimization complete.")
