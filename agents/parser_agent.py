import uuid
import datetime
import re
from flask import Flask, request, jsonify

app = Flask(__name__)

AGENT_NAME = "parser-agent"

# Utility to generate A2A response
def make_a2a_response(in_reply_to, payload):
    return {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "agent": AGENT_NAME,
        "in_reply_to": in_reply_to,
        "payload": payload
    }

# --- Core parsing logic ---
def parse_text(text: str):
    results = {
        "names": re.findall(r"[A-Z][a-z]+\s[A-Z][a-z]+", text),
        "emails": re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text),
        # Phone regex ko strict banaya (date format avoid karega)
        "phones": re.findall(r"\+?\d{1,3}[\s\-]?\d{2,4}[\s\-]?\d{3,4}[\s\-]?\d{3,4}", text),
        "dates": re.findall(r"\d{4}-\d{2}-\d{2}", text),
    }

    # Filter out dates accidentally matched as phones
    results["phones"] = [
        p for p in results["phones"] if not re.match(r"\d{4}-\d{2}-\d{2}", p)
    ]

    return results

# --- A2A Endpoint ---
@app.route("/a2a", methods=["POST"])
def a2a_endpoint():
    try:
        data = request.get_json(force=True)

        # Validate required fields
        if not data or "id" not in data or "agent" not in data or "payload" not in data:
            return jsonify({"error": "Invalid A2A request"}), 400

        in_reply_to = data.get("id")
        payload = data.get("payload", {})

        # Extract text
        text = payload.get("text", "")
        parsed = parse_text(text)

        # Build response
        response = make_a2a_response(in_reply_to, parsed)
        return jsonify(response), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print(f"🚀 Starting {AGENT_NAME} on http://127.0.0.1:5000/a2a")
    app.run(host="127.0.0.1", port=5000)

