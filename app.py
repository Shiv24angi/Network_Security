import sys
import os
from fastapi.responses import StreamingResponse
import io
import certifi
ca = certifi.where()

from dotenv import load_dotenv
load_dotenv()
mongo_db_url = os.getenv("MONGODB_URL_KEY")
print(mongo_db_url)
import pymongo
from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.logging.logger import logging
from networksecurity.pipeline.training_pipeline import TrainingPipeline

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, File, UploadFile,Request
from uvicorn import run as app_run
from fastapi.responses import Response
from starlette.responses import RedirectResponse
import pandas as pd

from networksecurity.utils.main_utils.utils import load_object

from networksecurity.utils.ml_utils.model.estimator import NetworkModel
from fastapi.templating import Jinja2Templates

client = pymongo.MongoClient(mongo_db_url, tlsCAFile=ca)

from networksecurity.constant.training_pipeline import DATA_INGESTION_COLLECTION_NAME
from networksecurity.constant.training_pipeline import DATA_INGESTION_DATABASE_NAME

database = client[DATA_INGESTION_DATABASE_NAME]
collection = database[DATA_INGESTION_COLLECTION_NAME]

app = FastAPI()
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up Jinja2 templates to serve HTML files
templates = Jinja2Templates(directory=".")

@app.get("/", tags=["UI"])
async def index(request: Request):
    """
    This endpoint serves the main user interface for file upload.
    """
    return templates.TemplateResponse("upload.html", {"request": request})

@app.get("/train")
async def train_route():
    try:
        train_pipeline=TrainingPipeline()
        train_pipeline.run_pipeline()
        return Response("Training is successful")
    except Exception as e:
        raise NetworkSecurityException(e,sys)
    
@app.post("/predict")
async def predict_route(request: Request,file: UploadFile = File(...)):
    try:
        df=pd.read_csv(file.file)
        preprocesor=load_object("final_model/preprocessor.pkl")
        final_model=load_object("final_model/model.pkl")
        network_model = NetworkModel(preprocessor=preprocesor,model=final_model)
        y_pred = network_model.predict(df)

        # Create a new DataFrame with a simplified view
        df['predicted_column'] = y_pred

        # Select only a few key columns for display
        display_df = df[['URL_Length', 'web_traffic', 'predicted_column']]

        # You could also add a column with a human-readable prediction
        display_df['prediction_label'] = display_df['predicted_column'].apply(
            lambda x: 'Malicious (Phishing)' if x == 1.0 else 'Legitimate'
        )

        table_html = display_df.to_html(classes='table table-striped')
        return templates.TemplateResponse("table.html", {"request": request, "table": table_html})
        
    except Exception as e:
        raise NetworkSecurityException(e,sys)
    
@app.post("/predict_csv")
async def predict_csv_route(file: UploadFile = File(...)):
    try:
        df=pd.read_csv(file.file)
        preprocesor=load_object("final_model/preprocessor.pkl")
        final_model=load_object("final_model/model.pkl")
        network_model = NetworkModel(preprocessor=preprocesor,model=final_model)
        y_pred = network_model.predict(df)
        df['predicted_column'] = y_pred

        # Use an in-memory buffer to create the CSV file
        stream = io.StringIO()
        df.to_csv(stream, index=False)
        
        # Create a response that will trigger a download in the user's browser
        response = StreamingResponse(
            iter([stream.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment;filename=predicted_output.csv"}
        )
        return response
        
    except Exception as e:
            raise NetworkSecurityException(e,sys)

    
if __name__=="__main__":
    app_run(app,host="localhost",port=8000)
