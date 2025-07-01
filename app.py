import openai
import os
import logging
import traceback
from flask import Flask, request, jsonify, abort
from flask_cors import CORS
from dotenv import load_dotenv
import sentencepiece as spm
import ctranslate2

# Load environment variables
load_dotenv()
api_key = os.getenv("KEY")

if not api_key:
    raise ValueError("Missing OpenAI API key (KEY) in environment variables.")

openai.api_key = api_key

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load models
sp_encode = spm.SentencePieceProcessor(model_file='spm_en.model')
sp_decode = spm.SentencePieceProcessor(model_file='spm_ata.model')
translator = ctranslate2.Translator("ctranslate_model", device="cpu")

@app.route("/")
def root():
    return jsonify({"message": "Hello, World!"})

@app.route("/translate/ata", methods=["GET"])
def get_translation():
    message = request.args.get("message", "").strip()
    if not message:
        abort(400, description="Query parameter 'message' cannot be empty.")

    try:
        response = openai.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "you are a translation tool that translates ata manobo to english. "
                        "respond only with the translated sentence. make all text lowercase. "
                        "the number and type of punctuation marks in the output must exactly match the input—"
                        "do not add, remove, or change any punctuation."
                        "add minor grammatical errors."
                    )
                },
                {
                    "role": "user",
                    "content": message
                }
            ]
        )
        translated = response.choices[0].message.content.strip()
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

        # Encode message using SentencePiece
        encoded = sp_encode.encode(message, out_type=str)
        logger.info("Encoded tokens: %s", encoded)

        # Perform translation using CTranslate2
        logger.info("Calling translator.translate_batch...")
        results = translator.translate_batch([encoded], beam_size=1)
        logger.info("Translation results: %s", results)

        # Get best translation
        translated_tokens = results[0].hypotheses[0]
        logger.info("Best hypothesis: %s", translated_tokens)

        # Decode using SentencePiece
        translation = sp_decode.decode(translated_tokens)
        logger.info("Final translation: %s", translation)

        return jsonify({"translation": translation})

    except Exception as e:
        logger.error("Error during translation in /translate/eng", exc_info=True)
        abort(500, description=str(e))

if __name__ == "__main__":
    app.run(debug=True)
