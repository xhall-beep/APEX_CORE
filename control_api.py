from flask import Flask, render_template, request, jsonify
import subprocess
import os

app = Flask(__name__, template_folder='./deliveries')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scout')
def scout():
    # Executes the Discovery Engine
    result = subprocess.check_output(['python3', 'discover_tools.py']).decode('utf-8')
    return jsonify({"status": "🔱 SCOUT COMPLETE", "output": result})

@app.route('/ingest', methods=['POST'])
def ingest():
    repo_url = request.json.get('url')
    # Executes the Ingestor
    subprocess.run(['./ingest_repo.sh', repo_url])
    return jsonify({"status": f"🔱 {repo_url} INGESTED"})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
