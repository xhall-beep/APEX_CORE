import requests
import os

def scout_github(query):
    print(f"🔱 SCOUTING GITHUB FOR: {query}...")
    url = f"https://api.github.com/search/repositories?q={query}+stars:>100&sort=stars"
    # Note: Using public API; for high-frequency scouting, we'll link your GH Token
    try:
        r = requests.get(url)
        repos = r.json().get('items', [])[:5]
        for repo in repos:
            print(f"🚀 FOUND: {repo['full_name']} - {repo['html_url']}")
            # One-click command ready for ingest_repo.sh
            print(f"👉 COMMAND: ./ingest_repo.sh {repo['clone_url']}")
    except Exception as e:
        print(f"⚠️ SCOUT ERROR: {e}")

if __name__ == "__main__":
    # Scouting based on your Secret Book's primary interests
    scout_github("pentesting-tool")
    scout_github("autonomous-agent")
