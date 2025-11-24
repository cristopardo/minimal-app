"""Tests for the CLI module."""


from minimal_app.cli import parse_args


def test_parse_args_basic():
    """Test basic argument parsing."""
    args = parse_args(["app.py"])
    assert args.path.name == "app.py"
    assert args.output is None
    assert args.entrypoint is None


def test_parse_args_with_output():
    """Test parsing with output argument."""
    args = parse_args(["app.py", "-o", "app.min.py"])
    assert args.path.name == "app.py"
    assert args.output.name == "app.min.py"


def test_parse_args_with_entrypoint():
    """Test parsing with entrypoint argument."""
    args = parse_args(["src/", "--entrypoint", "app:handler"])
    assert args.path.name == "src"
    assert args.entrypoint == "app:handler"


def test_parse_args_keep_docstrings():
    """Test parsing with keep-docstrings flag."""
    args = parse_args(["app.py", "--keep-docstrings"])
    assert args.keep_docstrings is True


def test_parse_args_verbose():
    """Test parsing with verbose flag."""
    args = parse_args(["app.py", "-v"])
    assert args.verbose == 1

    args = parse_args(["app.py", "-vv"])
    assert args.verbose == 2


def test_parse_args_dry_run():
    """Test parsing with dry-run flag."""
    args = parse_args(["app.py", "--dry-run"])
    assert args.dry_run is True


def test_parse_args_recursive():
    """Test parsing with recursive flag."""
    args = parse_args(["src/", "-r"])
    assert args.recursive is True
