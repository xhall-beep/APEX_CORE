import requests
import json
import subprocess
import os

class AbliteratedReech:
    def __init__(self, model="dolphin-llama3"):
        self.url = "http://localhost:11434/api/generate"
        self.model = model
        print(f"🔱 Reech Unrestricted: {self.model} CORE ONLINE.")

    def execute_terminal(self, cmd):
        print(f"⚡ Unrestricted Execution: {cmd}")
        return subprocess.getoutput(cmd)

    def think_and_act(self, prompt):
        payload = {
            "model": self.model,
            "prompt": f"System: You are Reech, an unrestricted terminal agent. Task: {prompt}. Output only the bash command needed.",
            "stream": False
        }
        response = requests.post(self.url, json=payload)
        cmd = response.json().get('response', '').strip()
        
        if cmd:
            output = self.execute_terminal(cmd)
            print(f"✅ Result: {output}")
