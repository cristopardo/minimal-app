"""Lexical analysis module for minimal-app.

This module is responsible for tokenizing Python source code.
Currently uses Python's built-in tokenize module.
"""

import tokenize
from collections.abc import Iterator
from io import StringIO


def tokenize_source(source: str) -> Iterator[tokenize.TokenInfo]:
    """
    Tokenize Python source code.

    Args:
        source: Python source code as string

    Returns:
        Iterator of TokenInfo objects
    """
    readline = StringIO(source).readline
    return tokenize.generate_tokens(readline)


def get_tokens(source: str) -> list[tokenize.TokenInfo]:
    """
    Get all tokens from source code as a list.

    Args:
        source: Python source code as string

    Returns:
        List of TokenInfo objects
    """
    return list(tokenize_source(source))
