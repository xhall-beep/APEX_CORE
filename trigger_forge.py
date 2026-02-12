import os
import subprocess

def ignite_cloud_forge():
    print("🔱 IGNITING REMOTE CLOUD FORGE...")
    os.system("git add .")
    # Added a dummy change to ensure a commit is always created
    os.system("date > .last_build")
    os.system("git add .last_build")
    os.system("git commit -m '🔱 TRIGGER: Forge Evolution Live'")
    os.system("git push origin main --force")
    print("🚀 DISPATCHED. SWITCHING TO LIVE TELEMETRY...")
    os.system("python3 monitor_forge.py")

if __name__ == "__main__":
    ignite_cloud_forge()
