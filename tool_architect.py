import os
import subprocess

def deploy_capability(repo_url, tool_name):
    print(f"🚀 ARCHITECT: FETCHING {tool_name.upper()}...")
    path = f"~/APEX_CORE/TOOLS/{tool_name}"
    os.system(f"mkdir -p ~/APEX_CORE/TOOLS")
    os.system(f"git clone {repo_url} {path} --quiet")
    print(f"✅ {tool_name.upper()} BONDED TO CORE.")

def main():
    print("🔱 REECH TOOL ARCHITECT: SCANNING FOR OPTIMAL REPOS...")
    # Targets for System Deep-Dives and Sub-Agent Construction
    repos = {
        "agent-framework": "https://github.com/assafelovic/gpt-researcher", # Autonomous Research
        "system-audit": "https://github.com/trimstray/the-book-of-secret-knowledge", # Knowledge Repository
        "auto-coder": "https://github.com/Significant-Gravitas/AutoGPT" # Agent Logic
    }
    
    for name, url in repos.items():
        deploy_capability(url, name)

    print("\n🔱 ALL CAPABILITIES SYNCED TO ~/APEX_CORE/TOOLS")
    os.system("termux-notification --title 'ARCHITECT COMPLETE' --content 'New tools bonded to rsa core.'")

if __name__ == "__main__":
    main()
