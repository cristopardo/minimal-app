"""Code generation module for minimal-app.

This module is responsible for generating optimized Python code from AST.
"""

import ast
from pathlib import Path


class CodeGenerator:
    """
    Generates Python code from AST with optional transformations.
    """

    def __init__(self, suffix: str = "__ma"):
        """
        Initialize code generator.

        Args:
            suffix: Suffix to append to renamed modules/functions
        """
        self.suffix = suffix

    def generate(self, tree: ast.Module) -> str:
        """
        Generate Python code from AST.

        Args:
            tree: AST Module node

        Returns:
            Python source code as string
        """
        # Ensure all nodes have proper location info
        ast.fix_missing_locations(tree)

        # Convert AST to source code
        return ast.unparse(tree)

    def generate_with_renaming(self, tree: ast.Module, module_name: str) -> str:
        """
        Generate code with renamed symbols (adds suffix).

        This is a placeholder for future implementation.

        Args:
            tree: AST Module node
            module_name: Original module name

        Returns:
            Python source code with renamed symbols
        """
        # Placeholder - real implementation would:
        # 1. Walk the AST
        # 2. Rename all relevant symbols with suffix
        # 3. Update all references
        # 4. Generate code

        return self.generate(tree)


def write_module(
    tree: ast.Module,
    output_path: Path,
    module_name: str,
    add_suffix: bool = False,
) -> None:
    """
    Write a module to disk.

    Args:
        tree: AST Module node
        output_path: Path to write to
        module_name: Name of the module
        add_suffix: Whether to add __ma suffix to symbols
    """
    generator = CodeGenerator()

    if add_suffix:
        code = generator.generate_with_renaming(tree, module_name)
    else:
        code = generator.generate(tree)

    # Create parent directories if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write code to file
    output_path.write_text(code, encoding="utf-8")
