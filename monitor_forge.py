import os
import time
import subprocess

def get_latest_action_status():
    # Uses GitHub CLI to get the status of the most recent run
    try:
        result = subprocess.check_output(["gh", "run", "list", "--limit", "1", "--json", "status,conclusion,id,status"], stderr=subprocess.STDOUT)
        import json
        data = json.loads(result)
        if data:
            return data[0]
    except Exception as e:
        return None

print("🔱 MONITORING LIVE FORGE PROGRESS...")

last_status = ""
while True:
    run = get_latest_action_status()
    if run:
        status = run['status']
        if status != last_status:
            print(f"🚀 CURRENT STAGE: {status.upper()}")
            last_status = status
        
        if status == "completed":
            print(f"✅ FORGE COMPLETE. CONCLUSION: {run['conclusion'].upper()}")
            break
    else:
        print("⏳ WAITING FOR RUN TO REGISTER...")
    
    time.sleep(5)
