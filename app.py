import os
import json
from flask import Flask, request, jsonify, abort
from flask_cors import CORS
from _service import service

app = Flask(__name__)
CORS(app)


# Load or initialize translation memory
TM_FILE = 'translation_memory.json'
if os.path.exists(TM_FILE):
    with open(TM_FILE, 'r', encoding='utf-8') as f:
        translation_memory = json.load(f)
else:
    translation_memory = {}

@app.route("/")
def root():
    return jsonify({"message": "Hello, World!"})

@app.route("/translate/ata", methods=["GET"])
def get_translation():
    message = request.args.get("message", "").strip()
    if not message:
        abort(400, description="Query parameter 'message' cannot be empty.")

    if message in translation_memory:
        return jsonify({"translation": translation_memory[message]})

    try:
        translated = service(message, translation_memory)

        return jsonify({"translation": translated})

    except Exception as e:
        abort(500, description=str(e))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
