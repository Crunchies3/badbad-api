import openai
from flask import Flask, request, jsonify, abort
from dotenv import load_dotenv
import os
from flask_cors import CORS
import sentencepiece as spm
import onmt.utils.parse
from onmt.translate.translator import build_translator

# Load environment variables
load_dotenv()
api_key = os.getenv("KEY")

if not api_key:
    raise ValueError("Missing OpenAI API key (KEY) in environment variables.")

# Set OpenAI API key
openai.api_key = api_key

# Initialize Flask app
app = Flask(__name__)
CORS(app)

sp_encode = spm.SentencePieceProcessor(model_file='spm_en.model')
sp_decode = spm.SentencePieceProcessor(model_file='spm_ata.model') 

translator_opts = onmt.utils.parse.ArgumentParser().parse_args_from_string([
    '-model', 'eng-ata/run/latest.pt',
    '-replace_unk',
    '-beam_size', '5',
    '-n_best', '1'
])

translator = build_translator(opt=translator_opts, report_score=False)

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
        # Encode the English input
        encoded = sp_encode.encode(message, out_type=str)
        tokenized_input = [" ".join(encoded)]  # OpenNMT expects space-delimited string

        # Translate using OpenNMT-py (in-memory)
        translations = translator.translate(
            src=tokenized_input,
            tgt=None,
            src_dir=None,
            batch_size=1,
            attn_debug=False
        )

        # Get top translation output
        translated_pieces = translations[0][0].split()

        # Decode using Ata SPM
        decoded = sp_decode.decode(translated_pieces)

        return jsonify({"translation": decoded})
    except Exception as e:
        abort(500, description=str(e))

if __name__ == "__main__":
    app.run(debug=True)
