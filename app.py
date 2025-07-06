import os
import logging
import json
from flask import Flask, request, jsonify, abort
from flask_cors import CORS
import sentencepiece as spm
import ctranslate2
from _service import service 
import socket

app = Flask(__name__)
CORS(app)

# Logging config
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# model for eng - ata
sp_encode = spm.SentencePieceProcessor(model_file='spm_en.model')
sp_decode = spm.SentencePieceProcessor(model_file='spm_ata.model')
translator = ctranslate2.Translator("ctranslate_model", device="cpu", compute_type="int8")

# model for ata - eng
ata_sp_encode = spm.SentencePieceProcessor(model_file='./ate-eng/spm_ata.model')
ata_sp_decode = spm.SentencePieceProcessor(model_file='./ate-eng/spm_en.model')
ata_translator = ctranslate2.Translator("ctranslate_model_ata_eng", device="cpu", compute_type="int8")


def is_online(host="8.8.8.8", port=53, timeout=3):
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except Exception:
        return False

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
        logger.info(f"Received input: {message}")

        if is_online():
            translated = service(message, translation_memory)
        else:
            encoded = ata_sp_encode.encode(message, out_type=str)
            results = ata_translator.translate_batch([encoded], beam_size=1, max_batch_size=1)
            translated_tokens = results[0].hypotheses[0]
            translated = ata_sp_decode.decode(translated_tokens)

        # Save to memory
        translation_memory[message] = translated
        with open(TM_FILE, 'w', encoding='utf-8') as f:
            json.dump(translation_memory, f, ensure_ascii=False, indent=2)

        return jsonify({"translation": translated})

    except Exception as e:
        logger.error("Error in /translate/ata", exc_info=True)
        abort(500, description=str(e))


@app.route("/translate/eng", methods=["GET"])
def translate_eng_to_ata():
    message = request.args.get("message", "").strip()
    if not message:
        abort(400, description="Query parameter 'message' cannot be empty.")

    try:
        logger.info(f"Received input: {message}")

        # Tokenize
        encoded = sp_encode.encode(message, out_type=str)
        logger.info("Encoded tokens: %s", encoded)

        # Translate
        results = translator.translate_batch([encoded], beam_size=1, max_batch_size=1)
        translated_tokens = results[0].hypotheses[0]

        # Detokenize
        translation = sp_decode.decode(translated_tokens)
        logger.info("Final translation: %s", translation)

        return jsonify({"translation": translation})

    except Exception as e:
        logger.error("Error during translation in /translate/eng", exc_info=True)
        abort(500, description=str(e))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
