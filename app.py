import os
import json
from flask import Flask, request, jsonify, abort, send_file
from _service import service
import logging
import mysql.connector
from contextlib import contextmanager

app = Flask(__name__)

# Simple CORS setup - remove Flask-CORS and do it manually
@app.after_request
def after_request(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, ngrok-skip-browser-warning, Cache-Control'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Max-Age'] = '86400'
    return response

# Handle preflight OPTIONS requests
@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = jsonify({})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, ngrok-skip-browser-warning, Cache-Control'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Max-Age'] = '86400'
        return response

logging.basicConfig(level=logging.INFO)

TM_FILE = 'translation_memory.json'
if os.path.exists(TM_FILE):
    with open(TM_FILE, 'r', encoding='utf-8') as f:
        translation_memory = json.load(f)
else:
    translation_memory = {}

@contextmanager
def mysql_connection():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="cyril2003!",
        database="badbad"
    )
    try:
        yield conn
    finally:
        conn.close()

@app.route("/")
def root():
    return jsonify({"message": "Hello, World!"})

@app.route("/add-phrase", methods=["POST"])
def upload_audio():
    audio_file = request.files.get("audio")
    user = request.form.get("user")
    ata_phrase = request.form.get("ata_phrase")
    eng_phrase = request.form.get("eng_phrase")
    if not audio_file:
        abort(400, description="No audio file provided.")
    if not user:
        abort(400, description="No user provided.")
    if not ata_phrase:
        abort(400, description="No ata_phrase provided.")
    if not eng_phrase:
        abort(400, description="No eng_phrase provided.")

    audio_dir = "audio"
    os.makedirs(audio_dir, exist_ok=True)
    base, ext = os.path.splitext(audio_file.filename)
    candidate = audio_file.filename
    audio_path = os.path.join(audio_dir, candidate)
    count = 1
    while os.path.exists(audio_path):
        candidate = f"{base}({count}){ext}"
        audio_path = os.path.join(audio_dir, candidate)
        count += 1
    audio_file.save(audio_path)
    audio_url = f"/audio/{candidate}"

    try:
        with mysql_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO tbl_phrases (user, ata_phrase, eng_phrase, audio_url, status) VALUES (%s, %s, %s, %s, %s)",
                (user, ata_phrase, eng_phrase, audio_url, "pending")
            )
            conn.commit()
            cursor.close()
    except Exception as e:
        abort(500, description=f"MySQL error: {e}")
    return jsonify({
        "message": "Audio uploaded successfully.",
        "audio_url": audio_url,
        "filename": audio_file.filename,
        "ata_phrase": ata_phrase,
        "eng_phrase": eng_phrase,
        "user": user
    })

@app.route("/get-phrase", methods=["GET"])
def get_phrase():
    phrase_id = request.args.get("id")
    filename = request.args.get("filename")
    if not phrase_id and not filename:
        abort(400, description="Query parameter 'id' or 'filename' is required.")
    try:
        with mysql_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            if phrase_id:
                cursor.execute("SELECT * FROM tbl_phrases WHERE id = %s", (phrase_id,))
            else:
                cursor.execute("SELECT * FROM tbl_phrases WHERE filename = %s", (filename,))
            result = cursor.fetchone()
            cursor.close()
            if not result:
                abort(404, description="Phrase not found.")
            return jsonify(result)
    except Exception as e:
        abort(500, description=f"MySQL error: {e}")

@app.route("/delete-phrase", methods=["DELETE"])
def delete_phrase():
    phrase_id = request.args.get("id")
    if not phrase_id:
        abort(400, description="Query parameter 'id' is required.")
    try:
        with mysql_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT audio_url FROM tbl_phrases WHERE id = %s", (phrase_id,))
            result = cursor.fetchone()
            if not result:
                cursor.close()
                abort(404, description="Phrase not found.")
            audio_url = result.get("audio_url")
            # Delete the phrase from the database
            cursor.execute("DELETE FROM tbl_phrases WHERE id = %s", (phrase_id,))
            conn.commit()
            cursor.close()
        # Delete the audio file if it exists
        if audio_url:
            filename = os.path.basename(audio_url)
            audio_path = os.path.join("audio", filename)
            if os.path.exists(audio_path):
                os.remove(audio_path)
        return jsonify({"message": "Phrase and audio file deleted successfully."})
    except Exception as e:
        abort(500, description=f"MySQL error: {e}")

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

@app.route("/all-phrases", methods=["GET"])
def get_all_phrases():
    try:
        with mysql_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM tbl_phrases")
            results = cursor.fetchall()
            cursor.close()
            return jsonify(results)
    except Exception as e:
        abort(500, description=f"MySQL error: {e}")

@app.route("/user-phrases", methods=["GET"])
def get_user_phrases():
    user = request.args.get("user")
    if not user:
        abort(400, description="Query parameter 'user' is required.")
    try:
        with mysql_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM tbl_phrases WHERE user = %s", (user,))
            results = cursor.fetchall()
            cursor.close()
            return jsonify(results)
    except Exception as e:
        abort(500, description=f"MySQL error: {e}")

@app.route("/status-phrases", methods=["GET"])
def get_status_phrases():
    status = request.args.get("status")
    if not status:
        abort(400, description="Query parameter 'status' is required.")
    try:
        with mysql_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM tbl_phrases WHERE status = %s", (status,))
            results = cursor.fetchall()
            cursor.close()
            return jsonify(results)
    except Exception as e:
        abort(500, description=f"MySQL error: {e}")

@app.route("/audio-by-url", methods=["GET"])
def get_audio_by_url():
    audio_url = request.args.get("audio_url")
    if not audio_url:
        abort(400, description="Query parameter 'audio_url' is required.")
    # Extract the filename from the URL (assuming /audio/filename or full URL)
    filename = os.path.basename(audio_url)
    audio_path = os.path.join("audio", filename)
    if not os.path.exists(audio_path):
        abort(404, description="Audio file not found.")
    return send_file(audio_path)

@app.route("/update-phrase", methods=["POST"])
def update_phrase():
    # Accept both form-data (for file upload) and JSON
    if request.content_type and request.content_type.startswith("multipart/form-data"):
        form = request.form
        files = request.files
        phrase_id = form.get("id")
        ata_phrase = form.get("ata_phrase")
        eng_phrase = form.get("eng_phrase")
        status = form.get("status")
        user = form.get("user")
        audio_file = files.get("audio")
    else:
        data = request.json or {}
        phrase_id = data.get("id")
        ata_phrase = data.get("ata_phrase")
        eng_phrase = data.get("eng_phrase")
        status = data.get("status")
        user = data.get("user")
        audio_file = None

    if not phrase_id:
        abort(400, description="Field 'id' is required.")

    # Prepare for audio file update
    new_audio_url = None
    old_audio_url = None
    if audio_file:
        # Get old audio_url from DB
        try:
            with mysql_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT audio_url FROM tbl_phrases WHERE id = %s", (phrase_id,))
                result = cursor.fetchone()
                cursor.close()
                if result:
                    old_audio_url = result.get("audio_url")
        except Exception as e:
            abort(500, description=f"MySQL error: {e}")
        # Save new file with unique name
        audio_dir = "audio"
        os.makedirs(audio_dir, exist_ok=True)
        base, ext = os.path.splitext(audio_file.filename)
        candidate = audio_file.filename
        audio_path = os.path.join(audio_dir, candidate)
        count = 1
        while os.path.exists(audio_path):
            candidate = f"{base}({count}){ext}"
            audio_path = os.path.join(audio_dir, candidate)
            count += 1
        audio_file.save(audio_path)
        new_audio_url = f"/audio/{candidate}"

    # Build dynamic update query
    fields = []
    values = []
    if ata_phrase is not None:
        fields.append("ata_phrase = %s")
        values.append(ata_phrase)
    if eng_phrase is not None:
        fields.append("eng_phrase = %s")
        values.append(eng_phrase)
    if new_audio_url is not None:
        fields.append("audio_url = %s")
        values.append(new_audio_url)
    if status is not None:
        fields.append("status = %s")
        values.append(status)
    if user is not None:
        fields.append("user = %s")
        values.append(user)
    if not fields:
        abort(400, description="No fields to update.")
    values.append(phrase_id)
    query = f"UPDATE tbl_phrases SET {', '.join(fields)} WHERE id = %s"
    try:
        with mysql_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(values))
            conn.commit()
            cursor.close()
        # Optionally delete old audio file if a new one was uploaded
        if audio_file and old_audio_url:
            old_filename = os.path.basename(old_audio_url)
            old_audio_path = os.path.join("audio", old_filename)
            if os.path.exists(old_audio_path):
                os.remove(old_audio_path)
        return jsonify({"message": "Phrase updated successfully."})
    except Exception as e:
        abort(500, description=f"MySQL error: {e}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
