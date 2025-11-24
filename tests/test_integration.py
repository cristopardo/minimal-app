"""Integration tests for minimal-app."""

import tempfile
from pathlib import Path

from minimal_app.minifier import minify_file


def test_minify_integration():
    """Test end-to-end minification."""
    source = '''"""Module docstring."""

def hello():
    """Function docstring."""
    return "Hello, World!"
'''

    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = Path(tmpdir) / "test.py"
        output_file = Path(tmpdir) / "test.min.py"

        # Write source
        input_file.write_text(source)

        # Minify
        minified = minify_file(input_file, output_file)

        # Verify output exists
        assert output_file.exists()

        # Verify docstrings removed
        assert '"""Module docstring."""' not in minified
        assert '"""Function docstring."""' not in minified

        # Verify function preserved
        assert "def hello():" in minified
        assert 'return "Hello, World!"' in minified or "return 'Hello, World!'" in minified


def test_minify_preserves_functionality():
    """Test that minified code is still valid Python."""
    source = '''
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

result = add(2, 3)
'''

    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = Path(tmpdir) / "test.py"
        output_file = Path(tmpdir) / "test.min.py"

        input_file.write_text(source)
        minified = minify_file(input_file, output_file)

        # Verify it's valid Python by compiling it
        compile(minified, "<string>", "exec")

        # Verify it works
        namespace: dict = {}
        exec(minified, namespace)
        assert namespace["result"] == 5
