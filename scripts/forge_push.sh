#!/bin/bash
cd ~/APEX_CORE
echo "🚀 [GRAND MASTER] Initiating Sovereign Uplink to xhall-beep..."

# Ensure GitHub Action build exists
mkdir -p .github/workflows

git add .
git commit -m "🔱 ApexYX V33: 100+ Repos & Omni-Capability Integrated"
git push -u origin main --force

echo "📡 [MONITOR] Uplink complete. Monitoring the Forge..."
while true; do
    clear
    echo "🔱 APEX SOVEREIGN LIVE MONITORING (V33.0)"
    echo "------------------------------------------------"
    gh run list --limit 1 --repo xhall-beep/ApexYX-Sovereign
    echo "------------------------------------------------"
    RUN_DATA=$(gh run list --limit 1 --repo xhall-beep/ApexYX-Sovereign --json status,conclusion)
    STATUS=$(echo $RUN_DATA | jq -r '.[0].status')
    CONCLUSION=$(echo $RUN_DATA | jq -r '.[0].conclusion')
    
    if [ "$STATUS" == "completed" ]; then
        echo "✅ FORGE RESULT: $CONCLUSION"
        break
    elif [ "$STATUS" == "in_progress" ]; then
        echo "⏳ Hammering Sovereignty into shape..."
    fi
    sleep 10
done
