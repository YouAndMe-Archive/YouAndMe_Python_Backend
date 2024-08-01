import os
from dotenv import load_dotenv
from flask import request, jsonify
import sqlite3
from youandme import image_processing_api, location_api
from flask_restx import Resource, fields
import requests
import json
import re


load_dotenv()
API_KEY = os.getenv("API_KEY")
API_URL = os.getenv("API_URL")
API_MODEL = os.getenv("API_MODEL")
API_PROMPT_TEMPLATE = os.getenv("API_PROMPT")
API_PURPOSE = os.getenv("API_PURPOSE")

# Request model for Swagger documentation
image_processing_model = image_processing_api.model(
    "ImageProcessing",
    {
        "type": fields.String(required=True, description="The type of processing"),
        "emotion": fields.String(required=True, description="The emotion to apply"),
        "voice_text": fields.String(required=True, description="The voice text to use"),
        "image_url": fields.String(
            required=True, description="The URL of the image to process"
        ),
    },
)

# Response model for Swagger documentation
response_model = image_processing_api.model(
    "Response", {"result": fields.Raw(description="The result from OpenAI API")}
)

@image_processing_api.route("/image-processing")
class ImageProcessing(Resource):
    @image_processing_api.expect(image_processing_model)
    @image_processing_api.response(200, "Success", response_model)
    @image_processing_api.response(500, "Internal Server Error")
    def post(self):
        input_data = request.get_json()

        type_ = input_data["type"]
        emotion = input_data["emotion"]
        voice_text = input_data["voice_text"]
        image_url = input_data["image_url"]

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}",
        }

        prompt = API_PROMPT_TEMPLATE.format(
            type_=type_, emotion=emotion, voice_text=voice_text
        )

        payload = {
            "model": API_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": f"{API_PURPOSE}",
                },
                {"role": "system", "content": f"image_url: {image_url}, detail: high"},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 1000,
        }

        try:
            response = requests.post(API_URL, headers=headers, json=payload)
            response.raise_for_status()
        except requests.RequestException as e:
            return (
                jsonify(
                    {
                        "error": "Failed to communicate with OpenAI API",
                        "details": str(e),
                    }
                ),
                500,
            )

        response_data = response.json()

        try:
            content = response_data["choices"][0]["message"]["content"]
            content_clean = re.sub(
                r"^```json|```$", "", content.strip(), flags=re.MULTILINE
            )
            content_json = json.loads(content_clean)
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            return (
                jsonify(
                    {
                        "error": "Failed to parse response from OpenAI API",
                        "details": str(e),
                    }
                ),
                500,
            )

        return jsonify({"result": content_json})


location_model = location_api.model(
    "location",
    {
        "latitude": fields.Float(required=True, description="latitude"),
        "longitude": fields.Float(required=True, description="longitude"),
    },
)

# Response model for Swagger documentation
location_response_model = location_api.model(
    "Response", {"result": fields.List(fields.Raw(), description="List of locations")}
)


@location_api.route("/locations")
class Location(Resource):

    @location_api.expect(location_model)
    @location_api.response(200, "Success", location_response_model)
    @location_api.response(500, "Internal Server Error")
    def get(self):
        input_data = request.get_json()

        latitude = input_data["latitude"]
        longitude = input_data["longitude"]

        # SQLite3 데이터베이스 연결
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        # ±5 범위 내의 데이터 조회
        query = """
        SELECT * FROM location
        WHERE latitude BETWEEN ? AND ? AND longitude BETWEEN ? AND ?
        """
        cursor.execute(
            query, (latitude - 0.1, latitude + 0.1, longitude - 0.1, longitude + 0.1)
        )
        rows = cursor.fetchall()

        # 결과를 JSON 형식으로 변환
        result = []
        for row in rows:
            result.append(
                {
                    "name": row[0],
                    "address1": row[1],
                    "address2": row[2],
                    "latitude": row[3],
                    "longitude": row[4],
                    "phone" : row[5],
                    "operation_time" : "추가"
                }
            )

        # 연결 종료
        conn.close()

        return jsonify({"result": result})
