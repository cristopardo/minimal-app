"""Semantic analysis module for minimal-app.

This module performs semantic analysis on Python AST to build:
- Symbol tables
- Call graphs
- Basic dependency tracking between functions/methods

It is intentionally conservative and focuses on patterns that are common
in typed, relatively "static" Python projects.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from typing import Dict, Set


@dataclass
class Symbol:
    """Represents a symbol in the symbol table."""

    name: str                    # short name (function, class, method)
    type: str                    # 'function', 'class', 'method'
    node: ast.AST                # AST node where it is defined
    module: str                  # module name, e.g. "app"
    defined_at: tuple[int, int]  # (line, column)
    used_by: set[str] = field(default_factory=set)  # fully-qualified callers


@dataclass
class CallGraph:
    """Represents a call graph for reachability analysis."""

    entrypoint: str                     # Format: "module:function"
    nodes: dict[str, Symbol] = field(default_factory=dict)   # fqname -> Symbol
    edges: dict[str, set[str]] = field(default_factory=dict) # caller -> callees
    reachable: set[str] = field(default_factory=set)         # set of fqnames


class SemanticAnalyzer(ast.NodeVisitor):
    """
    AST visitor for semantic analysis.

    Builds:
    - A symbol table (functions, classes, methods)
    - A local call graph (edges between symbols)
    """

    def __init__(self, module_name: str):
        self.module_name = module_name
        self.symbols: dict[str, Symbol] = {}
        self.current_class: str | None = None
        self.current_function: str | None = None

        # caller -> set(callees)
        self.edges: dict[str, set[str]] = {}

        # Very small import resolution:
        #   imports:   alias -> full_module_name
        #   from_imports: alias -> "module:symbol"
        self.imports: dict[str, str] = {}
        self.from_imports: dict[str, str] = {}

    # ------------------------------------------------------------------ helpers

    def _current_symbol_name(self) -> str | None:
        """Return fully-qualified name of the current function/method."""
        if self.current_function is None:
            return None
        if self.current_class:
            return f"{self.module_name}:{self.current_class}.{self.current_function}"
        return f"{self.module_name}:{self.current_function}"

    def _add_edge(self, callee: str) -> None:
        caller = self._current_symbol_name()
        if caller is None:
            # Call from module top-level: we ignore for now.
            return
        self.edges.setdefault(caller, set()).add(callee)

    # ---------------------------------------------------------------- definitions

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function or method definition."""
        if self.current_class:
            fqname = f"{self.module_name}:{self.current_class}.{node.name}"
            sym_type = "method"
        else:
            fqname = f"{self.module_name}:{node.name}"
            sym_type = "function"

        self.symbols[fqname] = Symbol(
            name=node.name,
            type=sym_type,
            node=node,
            module=self.module_name,
            defined_at=(node.lineno, node.col_offset),
        )

        old_func = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = old_func

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Treat async functions like normal ones, for our purposes."""
        self.visit_FunctionDef(node)  # same handling

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class definition."""
        fqname = f"{self.module_name}:{node.name}"

        self.symbols[fqname] = Symbol(
            name=node.name,
            type="class",
            node=node,
            module=self.module_name,
            defined_at=(node.lineno, node.col_offset),
        )

        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class

    # ----------------------------------------------------------------- imports

    def visit_Import(self, node: ast.Import) -> None:
        """Track 'import x' and 'import x as y'."""
        for alias in node.names:
            full_mod = alias.name  # e.g. "myapp.utils.io"
            if alias.asname:
                local_name = alias.asname
            else:
                # "import myapp.utils.io" binds "myapp" in code
                local_name = full_mod.split(".")[0]
            self.imports[local_name] = full_mod
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Track 'from m import f' and 'from m import f as g'."""
        if node.module is None:
            # Relative imports not handled for now
            return self.generic_visit(node)

        module = node.module
        for alias in node.names:
            name = alias.name
            local_name = alias.asname or name
            self.from_imports[local_name] = f"{module}:{name}"
        self.generic_visit(node)

    # ------------------------------------------------------------------- calls

    def visit_Call(self, node: ast.Call) -> None:
        """Record very approximate call edges."""
        func = node.func

        callee: str | None = None

        if isinstance(func, ast.Name):
            target = func.id
            # from-imported symbol?
            if target in self.from_imports:
                callee = self.from_imports[target]
            else:
                # assume local function in this module
                callee = f"{self.module_name}:{target}"

        elif isinstance(func, ast.Attribute):
            # something.method(...)
            if isinstance(func.value, ast.Name):
                base = func.value.id
                attr = func.attr
                # self.method(...) inside a class -> class.method
                if base == "self" and self.current_class:
                    callee = f"{self.module_name}:{self.current_class}.{attr}"
                # imported_module.function(...)
                elif base in self.imports:
                    mod = self.imports[base]
                    callee = f"{mod}:{attr}"

        if callee is not None:
            self._add_edge(callee)

        self.generic_visit(node)


# --------------------------------------------------------------------------- API


def analyze_module(tree: ast.Module, module_name: str) -> dict[str, Symbol]:
    """
    Analyze a module and return its symbol table.

    Args:
        tree: AST Module node
        module_name: Name of the module

    Returns:
        Dictionary mapping symbol names to Symbol objects
    """
    analyzer = SemanticAnalyzer(module_name)
    analyzer.visit(tree)
    return analyzer.symbols


def build_call_graph(
    modules: dict[str, ast.Module],
    entrypoint: str,
) -> CallGraph:
    """
    Build a call graph from an entrypoint.

    Args:
        modules: Dictionary mapping module names to AST nodes
        entrypoint: Entrypoint in format "module:function"

    Returns:
        CallGraph object
    """
    cg = CallGraph(entrypoint=entrypoint)

    # First, collect symbols and local edges from each module
    for module_name, tree in modules.items():
        analyzer = SemanticAnalyzer(module_name)
        analyzer.visit(tree)

        # Merge symbols
        for fqname, sym in analyzer.symbols.items():
            cg.nodes[fqname] = sym

        # Merge edges
        for caller, callees in analyzer.edges.items():
            cg.edges.setdefault(caller, set()).update(callees)

    # Populate used_by sets
    for caller, callees in cg.edges.items():
        for callee in callees:
            if callee in cg.nodes:
                cg.nodes[callee].used_by.add(caller)

    # Reachability from entrypoint
    start = entrypoint
    reachable: Set[str] = set()
    stack: list[str] = [start]

    while stack:
        symbol = stack.pop()
        if symbol in reachable:
            continue
        reachable.add(symbol)

        for callee in cg.edges.get(symbol, ()):
            if callee not in reachable:
                stack.append(callee)

    cg.reachable = reachable
    return cg


def compute_reachable_symbols(call_graph: CallGraph) -> set[str]:
    """
    Compute all symbols reachable from the entrypoint.

    We also ensure that:
    - If a method module:Class.method is reachable, we mark module:Class reachable.
    - If a class is reachable, we conservatively keep its __init__ if it exists.

    Args:
        call_graph: CallGraph object

    Returns:
        Set of reachable symbol names (fully-qualified)
    """
    reachable = set(call_graph.reachable)

    # If a method is reachable, keep the class symbol and its __init__ if present.
    extra: Set[str] = set()
    for fqname in list(reachable):
        # fqname format: "module:thing" or "module:Class.method"
        try:
            module, rest = fqname.split(":", 1)
        except ValueError:
            continue

        if "." in rest:
            class_name, method_name = rest.split(".", 1)
            class_sym = f"{module}:{class_name}"
            extra.add(class_sym)

            init_sym = f"{module}:{class_name}.__init__"
            if init_sym in call_graph.nodes:
                extra.add(init_sym)

    reachable |= extra
    return reachable
