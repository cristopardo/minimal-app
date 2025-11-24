"""Parser module for minimal-app.

This module is responsible for parsing Python source code into an AST.
Uses Python's built-in ast module.
"""

import ast
from pathlib import Path


def parse_source(source: str, filename: str = "<string>") -> ast.Module:
    """
    Parse Python source code into an AST.

    Args:
        source: Python source code as string
        filename: Optional filename for error messages

    Returns:
        AST Module node

    Raises:
        SyntaxError: If source code has syntax errors
    """
    return ast.parse(source, filename=filename, type_comments=True)


def parse_file(filepath: Path) -> ast.Module:
    """
    Parse a Python file into an AST.

    Args:
        filepath: Path to Python file

    Returns:
        AST Module node

    Raises:
        SyntaxError: If file has syntax errors
        FileNotFoundError: If file doesn't exist
    """
    source = filepath.read_text(encoding="utf-8")
    return parse_source(source, filename=str(filepath))


def unparse_ast(tree: ast.Module) -> str:
    """
    Convert an AST back to Python source code.

    Args:
        tree: AST Module node

    Returns:
        Python source code as string
    """
    return ast.unparse(tree)
