import requests, json, subprocess
from flask import Flask, request, jsonify

app = Flask(__name__)

class SovereignOrchestrator:
    def __init__(self, model="llama3.2:1b"):
        self.url = "http://localhost:11434/api/generate"
        self.model = model

    def query_brain(self, intent):
        payload = {"model": self.model, "prompt": intent, "stream": False}
        try:
            r = requests.post(self.url, json=payload, timeout=10)
            return r.json().get('response', 'Offline')
        except:
            return "Local Brain Congested - Switching to Cloud Power"

reech = SovereignOrchestrator()

@app.route('/orchestrate', methods=['POST'])
def handle():
    data = request.json
    return jsonify({"reech_output": reech.query_brain(data.get("intent"))})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5005)
