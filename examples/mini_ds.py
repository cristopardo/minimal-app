"""Example: mini_ds.py - A tiny DataFrame-like class."""


class MyDataFrame:
    """Tiny demo DataFrame-like class."""

    def __init__(self, data: list[int]) -> None:
        self.data: list[int] = data

    def head(self, n: int = 5) -> "MyDataFrame":
        """Return first n elements."""
        return MyDataFrame(self.data[:n])

    def tail(self, n: int = 5) -> "MyDataFrame":
        """Return last n elements."""
        return MyDataFrame(self.data[-n:])

    def sum(self) -> int:
        """Return the sum of all elements."""
        return sum(self.data)

    def unused(self) -> None:
        """This method is never called - dead code."""
        print("I am dead code")
