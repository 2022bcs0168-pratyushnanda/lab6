import os
import json
import joblib

from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score

from data_loader import load_data
from preprocessing import preprocess
from model import get_model


X, y = load_data("dataset/winequality-red.csv")

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

X_train, X_test = preprocess(X_train, X_test, scale=True)

model = get_model()
model.fit(X_train, y_train)

preds = model.predict(X_test)

mse = mean_squared_error(y_test, preds)
r2 = r2_score(y_test, preds)

os.makedirs("model", exist_ok=True)
os.makedirs("artifacts", exist_ok=True)

joblib.dump(model, "model/model.joblib")

metrics = {
    "mse": float(mse),
    "r2": float(r2)
}

with open("artifacts/metrics.json", "w") as f:
    json.dump(metrics, f, indent=4)

print(f"MSE={mse}")
print(f"R2={r2}")

