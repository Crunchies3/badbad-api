import os
import json
from flask import Flask, request, jsonify, abort, send_file
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

@app.route("/add-audio", methods=["POST"])
def upload_audio():
    audio_file = request.files.get("audio")
    if not audio_file:
        abort(400, description="No audio file provided.")
    audio_dir = "audio"
    os.makedirs(audio_dir, exist_ok=True)
    audio_path = os.path.join(audio_dir, audio_file.filename)
    audio_file.save(audio_path)
    audio_url = f"/audio/{audio_file.filename}"
    return jsonify({
        "message": "Audio uploaded successfully.",
        "audio_url": audio_url,
        "filename": audio_file.filename
    })

@app.route("/get-audio", methods=["GET"])
def get_audio():
    audio_filename = request.args.get("filename")
    if not audio_filename:
        abort(400, description="Query parameter 'filename' is required.")

    audio_path = os.path.join("audio", audio_filename)
    if not os.path.exists(audio_path):
        abort(404, description="Audio file not found.")

    return send_file(audio_path)


@app.route("/delete-audio", methods=["DELETE"])
def delete_audio():
    audio_filename = request.args.get("filename")
    if not audio_filename:
        abort(400, description="Query parameter 'filename' is required.")

    audio_path = os.path.join("audio", audio_filename)
    if not os.path.exists(audio_path):
        abort(404, description="Audio file not found.")

    os.remove(audio_path)
    return jsonify({"message": "Audio file deleted successfully."})


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
    app.run(host="0.0.0.0", port=5000, debug=True)
