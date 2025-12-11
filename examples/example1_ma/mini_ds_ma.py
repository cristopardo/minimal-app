class MyDataFrame:
    def __init__(self, data: list[int]) -> None:
        self.data = data

    def head(self, n: int = 5) -> "MyDataFrame":
        return MyDataFrame(self.data[:n])

    def sum(self) -> int:
        return sum(self.data)
