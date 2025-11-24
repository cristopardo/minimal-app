"""Tests for the minifier module."""


from minimal_app.minifier import minify_code


def test_remove_module_docstring():
    """Test that module docstrings are removed."""
    source = '''"""This is a module docstring."""

def foo():
    return 42
'''
    minified = minify_code(source, keep_docstrings=False)
    assert '"""This is a module docstring."""' not in minified
    assert "def foo():" in minified


def test_keep_module_docstring():
    """Test that module docstrings are kept when requested."""
    source = '''"""This is a module docstring."""

def foo():
    return 42
'''
    minified = minify_code(source, keep_docstrings=True)
    assert "This is a module docstring" in minified
    assert "def foo():" in minified


def test_remove_function_docstring():
    """Test that function docstrings are removed."""
    source = '''def foo():
    """This is a function docstring."""
    return 42
'''
    minified = minify_code(source, keep_docstrings=False)
    assert '"""This is a function docstring."""' not in minified
    assert "def foo():" in minified
    assert "return 42" in minified


def test_remove_class_docstring():
    """Test that class docstrings are removed."""
    source = '''class MyClass:
    """This is a class docstring."""

    def method(self):
        """Method docstring."""
        return 42
'''
    minified = minify_code(source, keep_docstrings=False)
    assert '"""This is a class docstring."""' not in minified
    assert '"""Method docstring."""' not in minified
    assert "class MyClass:" in minified
    assert "def method(self):" in minified


def test_preserve_string_literals():
    """Test that regular string literals are preserved."""
    source = '''def foo():
    message = "Hello, world!"
    return message
'''
    minified = minify_code(source, keep_docstrings=False)
    assert '"Hello, world!"' in minified or "'Hello, world!'" in minified


def test_empty_function_after_docstring_removal():
    """Test that functions with only docstrings get a pass statement."""
    source = '''def foo():
    """Only a docstring."""
'''
    minified = minify_code(source, keep_docstrings=False)
    assert "pass" in minified


def test_complex_code():
    """Test minification of more complex code."""
    source = '''"""Module for data processing."""

class MyDataFrame:
    """Tiny demo DataFrame-like class."""

    def __init__(self, data: list[int]) -> None:
        self.data: list[int] = data

    def head(self, n: int = 5) -> "MyDataFrame":
        """Return first n elements."""
        return MyDataFrame(self.data[:n])

    def sum(self) -> int:
        """Return the sum of all elements."""
        return sum(self.data)
'''
    minified = minify_code(source, keep_docstrings=False)

    # Docstrings should be removed
    assert "Module for data processing" not in minified
    assert "Tiny demo DataFrame-like class" not in minified
    assert "Return first n elements" not in minified

    # Code structure should be preserved
    assert "class MyDataFrame:" in minified
    assert "def __init__" in minified
    assert "def head" in minified
    assert "def sum" in minified
    assert "return sum(self.data)" in minified


def test_async_function_docstring():
    """Test that async function docstrings are removed."""
    source = '''async def foo():
    """Async function docstring."""
    return 42
'''
    minified = minify_code(source, keep_docstrings=False)
    assert '"""Async function docstring."""' not in minified
    assert "async def foo():" in minified
