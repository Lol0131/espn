# app.py
from flask import Flask, send_file, jsonify
from learningESPN import fetch_and_save_nfl
import os
from dotenv import load_dotenv  # pyright: ignore[reportMissingImports]
import traceback

# Load environment variables
load_dotenv()

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Check if .env file exists and API key is loaded
env_file = os.path.join(BASE_DIR, ".env")
if os.path.exists(env_file):
    api_key = os.getenv("OPENAI_API_KEY", "")
    if api_key and api_key != "your_openai_api_key_here":
        print(f"✓ OPENAI_API_KEY loaded (starts with: {api_key[:7]}...)")
    else:
        print("⚠ Warning: OPENAI_API_KEY not set or using placeholder value")
else:
    print("⚠ Warning: .env file not found. Create one with OPENAI_API_KEY=your_key_here")
@app.route('/')
def home():
    return send_file(os.path.join(BASE_DIR, "main.html"))

@app.route('/run', methods=['POST'])
def run():
    try:
        file_path = fetch_and_save_nfl()
        full_path = os.path.join(BASE_DIR, file_path)
        if os.path.exists(full_path):
            return jsonify({"status": "success", "message": "Analysis complete!"})
        else:
            return jsonify({"status": "error", "message": "File not created."}), 500
    except Exception as e:
        error_message = str(e)
        # Include more details in debug mode
        if app.debug:
            error_message += f"\n\nTraceback:\n{traceback.format_exc()}"
        print(f"Error in /run route: {error_message}")
        return jsonify({"status": "error", "message": error_message}), 500

@app.route('/download')
def download():
    file_path = os.path.join(BASE_DIR, "nfl_ai_summary.xlsx")
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True, download_name="nfl_ai_summary.xlsx")
    else:
        return jsonify({"status": "error", "message": "File not found. Make sure you clicked Start first."}), 404

if __name__ == "__main__":
    app.run(debug=True)

