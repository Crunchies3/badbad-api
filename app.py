from flask import Flask, request, jsonify, abort
from google import genai

app = Flask(__name__)

client = genai.Client(api_key="AIzaSyA2vAwOHZ4DP9CUwJonRRbVVuN6ZfohzEw")

@app.route("/")
def root():
    return jsonify({"Hello": "World"})

@app.route("/translate/ata")
def get_translation():
    message = request.args.get("message", "").strip()
    if not message:
        abort(400, description="message cannot be empty")
    
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=(
            f"translate the following ata-manobo sentence into english. provide only the translated sentence in plain text. "
            "do not add explanations or any extra text. keep the punctuation exactly as in the input—do not add, remove, or change it. "
            "english grammar does not need to be perfect. if there are any words you don’t know or are misspelled, keep them exactly as they appear "
            "in the original sentence without translating or correcting them. do not capitalize any words in the translation. "
            f"if the input is not a word, just output it back exactly as it is.: {message}"
        )
    )
    return jsonify({"translation": response.text})

if __name__ == "__main__":
    app.run()
