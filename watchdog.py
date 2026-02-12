import subprocess
import time
import os

def is_running(process_name):
    try:
        output = subprocess.check_output(["pgrep", "-f", process_name])
        return len(output) > 0
    except:
        return False

print("🔱 WATCHDOG ACTIVE: MONITORING SOVEREIGN CORE...")

while True:
    # Check Control API
    if not is_running("control_api.py"):
        print("⚠️ API DOWN. RESURRECTING...")
        subprocess.Popen(["python3", "control_api.py"])
    
    # Check Global Bridge (Cloudflared)
    if not is_running("cloudflared"):
        print("⚠️ BRIDGE DOWN. RE-IGNITING...")
        subprocess.Popen(["cloudflared", "tunnel", "--url", "http://localhost:8080"])
        
    time.sleep(10) # Audit every 10 seconds
