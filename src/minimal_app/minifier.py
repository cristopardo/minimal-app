"""Code minification using Python's AST module."""

import ast
from pathlib import Path


class MinifierTransformer(ast.NodeTransformer):
    """AST transformer that removes comments, docstrings, and unnecessary elements."""

    def __init__(self, keep_comments: bool = False, keep_docstrings: bool = False):
        self.keep_comments = keep_comments
        self.keep_docstrings = keep_docstrings

    def visit_Module(self, node: ast.Module) -> ast.Module:
        """Process module-level nodes."""
        if not self.keep_docstrings and node.body:
            # Remove module docstring (first statement if it's a string)
            if isinstance(node.body[0], ast.Expr) and isinstance(
                node.body[0].value, ast.Constant
            ):
                if isinstance(node.body[0].value.value, str):
                    node.body = node.body[1:]

        # Visit remaining nodes
        self.generic_visit(node)
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """Process function definitions."""
        if not self.keep_docstrings and node.body:
            # Remove function docstring
            if isinstance(node.body[0], ast.Expr) and isinstance(
                node.body[0].value, ast.Constant
            ):
                if isinstance(node.body[0].value.value, str):
                    node.body = node.body[1:]

        # If body is empty after removing docstring, add 'pass'
        if not node.body:
            node.body = [ast.Pass()]

        self.generic_visit(node)
        return node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AsyncFunctionDef:
        """Process async function definitions."""
        if not self.keep_docstrings and node.body:
            # Remove function docstring
            if isinstance(node.body[0], ast.Expr) and isinstance(
                node.body[0].value, ast.Constant
            ):
                if isinstance(node.body[0].value.value, str):
                    node.body = node.body[1:]

        # If body is empty after removing docstring, add 'pass'
        if not node.body:
            node.body = [ast.Pass()]

        self.generic_visit(node)
        return node

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:
        """Process class definitions."""
        if not self.keep_docstrings and node.body:
            # Remove class docstring
            if isinstance(node.body[0], ast.Expr) and isinstance(
                node.body[0].value, ast.Constant
            ):
                if isinstance(node.body[0].value.value, str):
                    node.body = node.body[1:]

        # If body is empty after removing docstring, add 'pass'
        if not node.body:
            node.body = [ast.Pass()]

        self.generic_visit(node)
        return node


def minify_code(
    source: str,
    keep_comments: bool = False,
    keep_docstrings: bool = False,
) -> str:
    """
    Minify Python source code by removing comments and docstrings.

    Args:
        source: Python source code as a string
        keep_comments: If True, preserve line comments (note: AST doesn't preserve comments)
        keep_docstrings: If True, preserve docstrings

    Returns:
        Minified Python source code

    Note:
        Python's AST module automatically strips comments during parsing,
        so keep_comments has no effect. To preserve comments, we would need
        to use a different approach (e.g., tokenize module).
    """
    # Parse the source code into an AST
    tree = ast.parse(source)

    # Apply transformations
    transformer = MinifierTransformer(
        keep_comments=keep_comments, keep_docstrings=keep_docstrings
    )
    transformed_tree = transformer.visit(tree)

    # Fix missing locations in the AST
    ast.fix_missing_locations(transformed_tree)

    # Convert back to source code
    minified = ast.unparse(transformed_tree)

    return minified


def minify_file(
    input_path: Path,
    output_path: Path | None = None,
    keep_comments: bool = False,
    keep_docstrings: bool = False,
) -> str:
    """
    Minify a Python file.

    Args:
        input_path: Path to input Python file
        output_path: Path to output file (if None, returns minified code without writing)
        keep_comments: If True, preserve line comments
        keep_docstrings: If True, preserve docstrings

    Returns:
        Minified Python source code
    """
    # Read source file
    source = input_path.read_text(encoding="utf-8")

    # Minify
    minified = minify_code(source, keep_comments, keep_docstrings)

    # Write to output if specified
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(minified, encoding="utf-8")

    return minified
