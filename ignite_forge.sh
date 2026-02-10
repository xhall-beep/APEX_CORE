#!/bin/bash
# Reech Autonomous Forge Igniter
echo "🚀 Initializing Sovereign Link..."

# 1. Clear existing broken remotes
git remote remove origin 2>/dev/null

# 2. Define target (Update 'YOUR_GITHUB_USERNAME' below)
USERNAME="YOUR_GITHUB_USERNAME"
REPO="APEX_CORE"
REMOTE_URL="https://github.com/$USERNAME/$REPO.git"

# 3. Clean the index of heavy build bloat to ensure a fast push
echo "🧹 Optimizing repository for transport..."
git rm -r --cached .buildozer/ 2>/dev/null
echo ".buildozer/" >> .gitignore

# 4. Finalize and Ignite
git add .
git commit -m "APEX CORE: Autonomous Cloud Forge Ignition" --allow-empty
git branch -M main
git remote add origin "$REMOTE_URL"

echo "🔥 Pushing to Cloud Forge at $REMOTE_URL..."
git push -u origin main --force

echo "✅ Ignition Complete. Cloud Forge is now building APEX CORE."
