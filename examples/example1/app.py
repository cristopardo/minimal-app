"""Example: app.py - Lambda-style handler."""

from mini_ds import MyDataFrame


def handler(event: dict, context: object) -> dict:
    """Lambda-style entrypoint."""
    df = MyDataFrame([1, 2, 3, 4, 5])
    head = df.head(3)
    return {"sum": head.sum()}
