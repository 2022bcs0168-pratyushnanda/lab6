import pandas as pd

def load_data(path: str):
    df = pd.read_csv(path, sep=";")
    X = df.drop("quality", axis=1)
    y = df["quality"]
    return X, y

