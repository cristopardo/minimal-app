"""Tree-shaking optimizer (placeholder - not yet implemented)."""

from pathlib import Path


def optimize_project(
    input_path: Path,
    output_path: Path | None,
    entrypoint: str,
    recursive: bool,
    keep_comments: bool,
    keep_docstrings: bool,
    dry_run: bool,
    verbose: int,
) -> None:
    """
    Optimize a project with tree-shaking from a single entrypoint.

    This is a placeholder implementation. Full tree-shaking requires:
    - Building a call graph from the entrypoint
    - Performing reachability analysis
    - Removing unreachable code
    - Renaming modules with __ma suffix

    Args:
        input_path: Input file or directory
        output_path: Output directory
        entrypoint: Entrypoint in format "module:function"
        recursive: Process directories recursively
        keep_comments: Keep line comments
        keep_docstrings: Keep docstrings
        dry_run: Don't write files, just show what would be done
        verbose: Verbosity level
    """
    print("⚠️  Tree-shaking optimization is not yet implemented.")
    print(f"   Entrypoint: {entrypoint}")
    print(f"   Input: {input_path}")
    print(f"   Output: {output_path}")
    print()
    print("This feature requires:")
    print("  - Semantic analysis to build a call graph")
    print("  - Reachability analysis from the entrypoint")
    print("  - Code elimination for unreachable functions/classes")
    print("  - Module renaming with __ma suffix")
    print()
    print("For now, only basic minification is supported.")
    print("Run without --entrypoint to minify files.")
