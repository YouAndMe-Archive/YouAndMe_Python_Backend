import os
import re
import json
import sqlite3
import requests
from dotenv import load_dotenv
from flask import request, jsonify
from flask_restx import Resource, fields
from youandme import image_processing_api, location_api

load_dotenv()

# 환경 변수 로드
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


def handle_api_error(e, message):
    return jsonify({"error": message, "details": str(e)}), 500


def call_openai_api(prompt, image_url):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    }

    payload = {
        "model": API_MODEL,
        "messages": [
            {"role": "system", "content": API_PURPOSE},
            {"role": "system", "content": f"image_url: {image_url}, detail: high"},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 600,
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()
        response_data = response.json()  # JSON 변환
        print(response_data)  # 응답 데이터 출력
        return response_data
    except requests.RequestException as e:
        raise Exception("Failed to communicate with OpenAI API") from e

@image_processing_api.route("/image-processing")
class ImageProcessing(Resource):
    @image_processing_api.expect(image_processing_model)
    @image_processing_api.response(200, "Success", response_model)
    @image_processing_api.response(500, "Internal Server Error")
    def post(self):
        input_data = request.get_json()

        prompt = API_PROMPT_TEMPLATE.format(
            type_=input_data["type"],
            emotion=input_data["emotion"],
            voice_text=input_data["voice_text"],
        )

        try:
            response_data = call_openai_api(prompt, input_data["image_url"])

            # 응답 데이터 검증
            if "choices" not in response_data or not response_data["choices"]:
                raise ValueError("Invalid response structure from OpenAI API")

            content = response_data["choices"][0]["message"]["content"]
            content_clean = re.sub(
                r"^```json|```$", "", content.strip(), flags=re.MULTILINE
            )

            # JSON 형식 검증
            try:
                content_json = json.loads(content_clean)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON format: {e}")

            return jsonify({"result": content_json})

        except (KeyError, IndexError, json.JSONDecodeError) as e:
            return handle_api_error(e, "Failed to parse response from OpenAI API")
        except Exception as e:
            return handle_api_error(e, "Error occurred while processing the image")


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


def fetch_locations(latitude, longitude):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    query = """
    SELECT * FROM location
    WHERE latitude BETWEEN ? AND ? AND longitude BETWEEN ? AND ?
    """
    cursor.execute(
        query, (latitude - 0.1, latitude + 0.1, longitude - 0.1, longitude + 0.1)
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


@location_api.route("/locations")
class Location(Resource):
    @location_api.expect(location_model)
    @location_api.response(200, "Success", location_response_model)
    @location_api.response(500, "Internal Server Error")
    def get(self):
        input_data = request.get_json()
        latitude = input_data["latitude"]
        longitude = input_data["longitude"]

        try:
            rows = fetch_locations(latitude, longitude)
            result = [
                {
                    "id": index,  # 인덱스 값을 추가
                    "facility_name": row[0],
                    "road_name_addr": row[1],
                    "number_addr": row[2],
                    "latitude": row[3],
                    "longitude": row[4],
                    "phone_number": row[5],
                    "operation_time": "월~금 09:00~18:00",
                }
                for index, row in enumerate(
                    rows
                )  # enumerate로 인덱스와 값 함께 가져오기
            ]
            return jsonify({"result": result})
        except Exception as e:
            return handle_api_error(e, "Error occurred while fetching locations")
