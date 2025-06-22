import openai
from flask import Flask, request, jsonify, abort
from dotenv import load_dotenv
import os
import subprocess
import tempfile
from flask_cors import CORS
import sentencepiece as spm

# Load environment variables
load_dotenv()
api_key = os.getenv("KEY")

if not api_key:
    raise ValueError("Missing OpenAI API key (KEY) in environment variables.")

openai.api_key = api_key

app = Flask(__name__)
CORS(app)

sp_encode = spm.SentencePieceProcessor(model_file='spm_en.model')
sp_decode = spm.SentencePieceProcessor(model_file='spm_ata.model')

MODEL_PATH = "latest.pt"

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
        abort(500, description=str(e))


@app.route("/translate/eng", methods=["GET"])
def translate_eng_to_ata():
    message = request.args.get("message", "").strip()
    if not message:
        abort(400, description="Query parameter 'message' cannot be empty.")

    try:
        # Encode using SentencePiece
        encoded = sp_encode.encode(message, out_type=str)
        tokenized_input = " ".join(encoded)

        # Write tokenized input to temporary file with UTF-8 encoding
        with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".txt", encoding="utf-8") as src_file:
            src_file.write(tokenized_input + "\n")
            src_file_path = src_file.name

        # Prepare output file path
        with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".txt", encoding="utf-8") as out_file:
            out_file_path = out_file.name

        # Call onmt_translate via subprocess
        command = [
            "onmt_translate",
            "-model", MODEL_PATH,
            "-src", src_file_path,
            "-output", out_file_path,
            "-replace_unk",
            "-beam_size", "5",
            "-n_best", "1"
        ]

        subprocess.run(command, check=True)

        # Read translated output (UTF-8)
        with open(out_file_path, "r", encoding="utf-8") as f:
            translated_tokens = f.read().strip().split()

        # Decode using SentencePiece
        translation = sp_decode.decode(translated_tokens)

        # Cleanup temp files
        os.remove(src_file_path)
        os.remove(out_file_path)

        return jsonify({"translation": translation})

    except subprocess.CalledProcessError as e:
        abort(500, description=f"Translation process failed: {e}")
    except Exception as e:
        abort(500, description=str(e))


if __name__ == "__main__":
    app.run(debug=True)
