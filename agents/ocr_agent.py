# Importing necessary libraries

from flask import Flask, request, jsonify
import requests
import base64
import mimetypes
import os
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

IMAGE_PATH = "uploads/receipt.jpeg" # For testing purposes

# Agent Card metadata for discovery
AGENT_CARD = {
    "name": "OCRAgent",
    "description": "Agent that performs OCR on base64-encoded images.",
    "url": "http://localhost:5001",
    "version": "1.0",
    "capabilities": {
        "streaming": False,
        "pushNotifications": False,
    }
}

@app.get("/.well-known/agent.json")
def get_agent_card():
    return jsonify(AGENT_CARD)

def encode_image_to_data_url(image_path: str) -> dict:
    mimetype, _ = mimetypes.guess_type(image_path)
    if mimetype is None:
        raise ValueError("Could not determine the MIME type of the image.")
    with open(image_path, "rb") as image_file:
        encoded = base64.b64encode(image_file.read()).decode("utf-8")
        return {
            "type": "image_url",
            "image_url": f"data:{mimetype};base64,{encoded}"
        }

def ocr_request(image_path):
    response = requests.post(
        "https://api.aimlapi.com/v1/ocr",
        headers={
            "Authorization": f"Bearer {os.getenv('API_KEY')}",
            "Content-Type": "application/json",
        },
        json={
            "document": encode_image_to_data_url(image_path),
            "model": "mistral/mistral-ocr-latest",
        },
    )
    data = response.json()
    return data

@app.post("/tasks/send")
def handle_task():
    task_request = request.get_json()
    task_id = task_request.get("id")
    try:
        user_message = task_request["message"]["parts"][0]["text"]
    except Exception:
        return jsonify({"error": "Invalid request format"}), 400

    # For this example, assume the user_message is the image path for OCR
    # In a real scenario, you might receive the image as a base64 payload or URL.
    try:
        ocr_result = ocr_request(user_message)
        ocr_text = ocr_result['pages'][0]['markdown']
    except Exception as e:
        ocr_text = f"OCR processing failed: {str(e)}"

    response_task = {
        "id": task_id,
        "status": {"state": "completed"},
        "messages": [
            task_request.get("message", {}),
            {
                "role": "agent",
                "parts": [{"text": ocr_text}]
            }
        ]
    }
    return jsonify(response_task)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
