from flask import Flask
from flask_cors import CORS
from flask_restx import Api

app = Flask(__name__)
api = Api(
    app,
    version="1.0",
    title="너나들이 API 문서",
    description="너나들이 OPENAI API 문서",
    doc="/api-docs",
)
image_processing_api = api.namespace("api/v1", description="Flask API")
location_api = api.namespace("api/v1", description="Flask API")
CORS(app, resources={r'*': {'origins': 'https://www.re-bom.shop/'}})

from youandme.apis import *  # apis import
