"""Command-line interface for minimal-app."""

import argparse
import sys
from pathlib import Path

from minimal_app import __version__
from minimal_app.minifier import minify_file
from minimal_app.optimizer import optimize_project


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="minimal-app",
        description="A compiler-inspired optimizer for statically typed Python",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("path", type=Path, help="File or directory to optimize")

    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output file or directory (default: overwrite in-place)",
    )

    parser.add_argument(
        "--entrypoint",
        type=str,
        metavar="MOD:FUNC",
        help="Single entrypoint for reachability analysis (required for tree-shaking)",
    )

    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Process directories recursively",
    )

    parser.add_argument(
        "--keep-comments",
        action="store_true",
        help="Keep line comments (docstrings are still removed)",
    )

    parser.add_argument(
        "--keep-docstrings",
        action="store_true",
        help="Keep docstrings (by default they are removed)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show a summary of planned changes without writing files",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase log verbosity (can be used multiple times)",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    return parser.parse_args(args)


def process_single_file(
    input_path: Path,
    output_path: Path | None,
    keep_comments: bool,
    keep_docstrings: bool,
    dry_run: bool,
    verbose: int,
) -> None:
    """Process a single Python file."""
    if verbose > 0:
        print(f"Processing: {input_path}")

    try:
        minified = minify_file(
            input_path,
            output_path if not dry_run else None,
            keep_comments=keep_comments,
            keep_docstrings=keep_docstrings,
        )

        if dry_run:
            print(f"\n{'=' * 60}")
            print(f"File: {input_path}")
            print(f"{'=' * 60}")
            print(minified)
            print(f"{'=' * 60}\n")
        elif verbose > 0:
            output = output_path or input_path
            print(f"  → Written to: {output}")

    except SyntaxError as e:
        print(f"Error parsing {input_path}: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error processing {input_path}: {e}", file=sys.stderr)
        sys.exit(1)


def process_directory(
    input_dir: Path,
    output_dir: Path | None,
    recursive: bool,
    keep_comments: bool,
    keep_docstrings: bool,
    dry_run: bool,
    verbose: int,
) -> None:
    """Process all Python files in a directory."""
    pattern = "**/*.py" if recursive else "*.py"
    py_files = list(input_dir.glob(pattern))

    if not py_files:
        print(f"No Python files found in {input_dir}", file=sys.stderr)
        sys.exit(1)

    if verbose > 0:
        print(f"Found {len(py_files)} Python file(s)")

    for py_file in py_files:
        # Calculate relative path and output path
        rel_path = py_file.relative_to(input_dir)
        out_path = output_dir / rel_path if output_dir else py_file

        process_single_file(
            py_file,
            out_path,
            keep_comments,
            keep_docstrings,
            dry_run,
            verbose,
        )


def main() -> None:
    """Main entry point for the CLI."""
    args = parse_args()

    # Validate input path
    if not args.path.exists():
        print(f"Error: Path does not exist: {args.path}", file=sys.stderr)
        sys.exit(1)

    # If entrypoint is provided, use the optimizer (tree-shaking)
    if args.entrypoint:
        if args.verbose > 0:
            print(f"Running with entrypoint: {args.entrypoint}")
            print("Note: Tree-shaking is not yet fully implemented.")

        optimize_project(
            input_path=args.path,
            output_path=args.output,
            entrypoint=args.entrypoint,
            recursive=args.recursive,
            keep_comments=args.keep_comments,
            keep_docstrings=args.keep_docstrings,
            dry_run=args.dry_run,
            verbose=args.verbose,
        )
    else:
        # Simple minification without tree-shaking
        if args.path.is_file():
            process_single_file(
                args.path,
                args.output,
                args.keep_comments,
                args.keep_docstrings,
                args.dry_run,
                args.verbose,
            )
        elif args.path.is_dir():
            if args.output and not args.dry_run:
                args.output.mkdir(parents=True, exist_ok=True)

            process_directory(
                args.path,
                args.output,
                args.recursive,
                args.keep_comments,
                args.keep_docstrings,
                args.dry_run,
                args.verbose,
            )
        else:
            print(f"Error: Invalid path type: {args.path}", file=sys.stderr)
            sys.exit(1)

    if args.verbose > 0:
        print("Done!")


if __name__ == "__main__":
    main()
