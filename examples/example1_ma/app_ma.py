from examples.example1_ma.mini_ds_ma import MyDataFrame

def handler(event: dict, context: object) -> dict:
    df = MyDataFrame([1, 2, 3, 4, 5])
    head = df.head(3)
    return {"sum": head.sum()}