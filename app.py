# app.py
from flask import Flask, send_file
from learnespn import fetch_and_save_nfl
import os

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
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
@app.route('/')
def home():
    return send_file(os.path.join(BASE_DIR, "main.html"))

@app.route('/run', methods=['POST'])
def run():
    try:
        file_path = fetch_and_save_nfl()
        if os.path.exists(file_path):
            return "OK"
        else:
            return "Error: File not created."
    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/download')
def download():
    file_path = os.path.join(BASE_DIR, "nfl_ai_summary.xlsx")
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return "Error: File not found. Make sure you clicked Start first."

if __name__ == "__main__":
    app.run(debug=True)

