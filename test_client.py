# test_client.py
import requests
import uuid

url = "http://127.0.0.1:5000/a2a"

data = {
    "id": str(uuid.uuid4()),
    "agent": "test-client",
    "payload": {
        "text": "John Doe email: john.doe@example.com phone: +123 456 7890 date: 2025-09-21"
    }
}

response = requests.post(url, json=data)
print("Status Code:", response.status_code)
print("Response:", response.json())
