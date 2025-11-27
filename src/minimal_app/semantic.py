"""Semantic analysis module for minimal-app.

This module performs semantic analysis on Python AST to build:
- Symbol tables
- Type information
- Call graphs
- Dependency tracking

Currently a placeholder for future implementation.
"""

import ast
from dataclasses import dataclass, field


@dataclass
class Symbol:
    """Represents a symbol in the symbol table."""

    name: str
    type: str  # 'function', 'class', 'method', 'variable'
    node: ast.AST
    module: str
    defined_at: tuple[int, int]  # (line, column)
    used_by: set[str] = field(default_factory=set)


@dataclass
class CallGraph:
    """Represents a call graph for reachability analysis."""

    entrypoint: str  # Format: "module:function"
    nodes: dict[str, Symbol] = field(default_factory=dict)
    edges: dict[str, set[str]] = field(default_factory=dict)  # caller -> callees
    reachable: set[str] = field(default_factory=set)


class SemanticAnalyzer(ast.NodeVisitor):
    """
    AST visitor for semantic analysis.

    Builds symbol tables and call graphs for tree-shaking.
    """

    def __init__(self, module_name: str):
        self.module_name = module_name
        self.symbols: dict[str, Symbol] = {}
        self.current_class: str | None = None
        self.current_function: str | None = None

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definition."""
        symbol_name = f"{self.module_name}:{node.name}"
        if self.current_class:
            symbol_name = f"{self.module_name}:{self.current_class}.{node.name}"

        self.symbols[symbol_name] = Symbol(
            name=node.name,
            type="method" if self.current_class else "function",
            node=node,
            module=self.module_name,
            defined_at=(node.lineno, node.col_offset),
        )

        old_function = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = old_function

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class definition."""
        symbol_name = f"{self.module_name}:{node.name}"

        self.symbols[symbol_name] = Symbol(
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

    This is a placeholder implementation.

    Args:
        modules: Dictionary mapping module names to AST nodes
        entrypoint: Entrypoint in format "module:function"

    Returns:
        CallGraph object
    """
    # Placeholder - real implementation would:
    # 1. Parse entrypoint
    # 2. Find all function calls from entrypoint
    # 3. Recursively build call graph
    # 4. Mark reachable nodes

    return CallGraph(entrypoint=entrypoint)


def compute_reachable_symbols(call_graph: CallGraph) -> set[str]:
    """
    Compute all symbols reachable from the entrypoint.

    This is a placeholder implementation.

    Args:
        call_graph: CallGraph object

    Returns:
        Set of reachable symbol names
    """
    # Placeholder - real implementation would:
    # 1. Start from entrypoint
    # 2. Do BFS/DFS to find all reachable nodes
    # 3. Return set of reachable symbol names

    return set()
