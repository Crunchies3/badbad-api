import os
import json
from flask import Flask, request, jsonify, abort
from flask_cors import CORS
from _service import service
import logging

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)

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
    message = request.args.get("message", "").strip().lower()
    if not message:
        abort(400, description="Query parameter 'message' cannot be empty.")

    if message in translation_memory:
        return jsonify({"translation": translation_memory[message]})

    # If all words are in memory, return word-by-word translation
    words = message.split()
    if all(word in translation_memory for word in words):
        word_translations = [translation_memory[word] for word in words]
        joined_translation = " ".join(word_translations)
        # Ask ChatGPT to fix the sentence based on context, using the [WORD_BY_WORD] flag
        try:
            flagged_translation = f"[WORD_BY_WORD] {joined_translation}"
            fixed_translation = service(flagged_translation, translation_memory)
            return jsonify({"translation": fixed_translation})
        except Exception as e:
            # If ChatGPT fails, return the raw joined translation
            return jsonify({"translation": joined_translation})

    # Otherwise, use ChatGPT to translate the whole message
    try:
        logging.info("Using ChatGPT for translation of message: '%s'", message)
        translated = service(message, translation_memory)
        return jsonify({"translation": translated})
    except Exception as e:
        abort(500, description=str(e))

if __name__ == "__main__":
    app.run(debug=True)
