"""minimal-app: A compiler-inspired optimizer for statically typed Python."""

__version__ = "0.1.0"

# Core functionality
# Modules (available for import)
from minimal_app import codegen, lexer, optimizer, parser, semantic
from minimal_app.minifier import minify_code, minify_file

__all__ = [
    # Version
    "__version__",
    # Main API
    "minify_code",
    "minify_file",
    # Modules
    "lexer",
    "parser",
    "semantic",
    "optimizer",
    "codegen",
]
