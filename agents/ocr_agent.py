import requests
import base64
import mimetypes

# getting api key from .env file
from dotenv import load_dotenv
import os

IMAGE_PATH = "uploads/receipt.jpeg"  # Replace with your image path

def encode_image_to_data_url(image_path: str) -> dict:
    """
    Reads an image from disk and returns a dict with a Base64-encoded data URL.

    Args:
        image_path (str): Path to the image file.

    Returns:
        dict: Dictionary with image data URL formatted for APIs like OpenAI.
    """
    # Guess the MIME type (e.g., image/jpeg, image/png)
    mimetype, = mimetypes.guess_type(image_path)
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

    # response.raise_for_status()
    data = response.json()
    
    return data


if __name__ == "__main__":
    print(ocr_request(IMAGE_PATH)['pages'][0]['markdown'])