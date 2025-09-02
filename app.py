import sys
import os
import io
import certifi
import pandas as pd
import pymongo

from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from starlette.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from uvicorn import run as app_run

from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.logging.logger import logging
from networksecurity.pipeline.training_pipeline import TrainingPipeline
from networksecurity.utils.main_utils.utils import load_object
from networksecurity.utils.ml_utils.model.estimator import NetworkModel
from networksecurity.constant.training_pipeline import (
    DATA_INGESTION_COLLECTION_NAME,
    DATA_INGESTION_DATABASE_NAME,
)

# Load environment variables
load_dotenv()
mongo_db_url = os.getenv("MONGODB_URL_KEY")
ca = certifi.where()

# Connect to MongoDB
client = pymongo.MongoClient(mongo_db_url, tlsCAFile=ca)
database = client[DATA_INGESTION_DATABASE_NAME]
collection = database[DATA_INGESTION_COLLECTION_NAME]

# FastAPI setup
app = FastAPI()
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Jinja2 templates setup
templates = Jinja2Templates(directory=".")

# ---------------- ROUTES ---------------- #

@app.get("/", tags=["UI"])
async def landing_page(request: Request):
    """
    Landing page (Welcome page).
    """
    return templates.TemplateResponse("landing.html", {"request": request})


@app.get("/upload", tags=["UI"])
async def upload_page(request: Request):
    """
    Upload page route for CSV upload.
    """
    return templates.TemplateResponse("upload.html", {"request": request})


@app.get("/train", tags=["Pipeline"])
async def train_route():
    """
    Run the training pipeline manually.
    """
    try:
        train_pipeline = TrainingPipeline()
        train_pipeline.run_pipeline()
        return Response("✅ Training is successful")
    except Exception as e:
        raise NetworkSecurityException(e, sys)


@app.post("/predict", tags=["Prediction"])
async def predict_route(request: Request, file: UploadFile = File(...)):
    """
    Predict and render results as an HTML table.
    """
    try:
        df = pd.read_csv(file.file)

        # Load preprocessor and model
        preprocessor = load_object("final_model/preprocessor.pkl")
        final_model = load_object("final_model/model.pkl")
        network_model = NetworkModel(preprocessor=preprocessor, model=final_model)

        # Predictions
        y_pred = network_model.predict(df)
        df["predicted_column"] = y_pred

        # Select key columns for display
        display_df = df[["URL_Length", "web_traffic", "predicted_column"]]
        display_df["prediction_label"] = display_df["predicted_column"].apply(
            lambda x: "Malicious (Phishing)" if x == 1.0 else "Legitimate"
        )

        # Convert to HTML table
        table_html = display_df.to_html(classes="table table-striped", index=False)
        return templates.TemplateResponse("table.html", {"request": request, "table": table_html})

    except Exception as e:
        raise NetworkSecurityException(e, sys)


@app.post("/predict_csv", tags=["Prediction"])
async def predict_csv_route(file: UploadFile = File(...)):
    """
    Predict and return results as downloadable CSV.
    """
    try:
        df = pd.read_csv(file.file)

        # Load preprocessor and model
        preprocessor = load_object("final_model/preprocessor.pkl")
        final_model = load_object("final_model/model.pkl")
        network_model = NetworkModel(preprocessor=preprocessor, model=final_model)

        # Predictions
        y_pred = network_model.predict(df)
        df["predicted_column"] = y_pred

        # Stream CSV output
        stream = io.StringIO()
        df.to_csv(stream, index=False)

        response = StreamingResponse(
            iter([stream.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment;filename=predicted_output.csv"},
        )
        return response

    except Exception as e:
        raise NetworkSecurityException(e, sys)


# ---------------- MAIN ---------------- #

if __name__ == "__main__":
    app_run(app, host="localhost", port=8000)
