import openai
from flask import Flask, request, jsonify, abort
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
api_key = os.getenv("KEY")

if not api_key:
    raise ValueError("Missing OpenAI API key (KEY) in environment variables.")

# Set OpenAI API key
openai.api_key = api_key

app = Flask(__name__)

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

if __name__ == "__main__":
    app.run(debug=True)
