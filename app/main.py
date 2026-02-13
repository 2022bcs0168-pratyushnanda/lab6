import joblib
import numpy as np
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.schema import WineInput

NAME = "Pratyush Nanda"
ROLL_NO = "2022BCS0168"

app = FastAPI(title="Wine Quality Prediction API")

model = joblib.load("model/model.joblib")

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs", status_code=301)

@app.post("/predict")
def predict(data: WineInput):
    features = np.array([[
        data.fixed_acidity,
        data.volatile_acidity,
        data.citric_acid,
        data.residual_sugar,
        data.chlorides,
        data.free_sulfur_dioxide,
        data.total_sulfur_dioxide,
        data.density,
        data.pH,
        data.sulphates,
        data.alcohol
    ]])

    prediction = model.predict(features)[0]

    return {
        "name": NAME,
        "roll_no": ROLL_NO,
        "wine_quality": int(round(float(prediction)))
    }

