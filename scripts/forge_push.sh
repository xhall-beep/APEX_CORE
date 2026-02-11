#!/bin/bash
cd ~/APEX_CORE
echo "🚀 [REECH] Purging metadata and forcing Grand Master Uplink..."
find tools -name ".git" -type d -exec rm -rf {} + 2>/dev/null
git add .
git commit -m "🔱 ApexYX V35.2: Omni-Manifest Engaged"
git push -u origin main --force
echo "📡 [MONITOR] Watching the Forge Heartbeat..."
while true; do
    clear
    echo "🔱 APEX SOVEREIGN LIVE MONITORING (V35.2)"
    echo "------------------------------------------------"
    gh run list --limit 1 --repo xhall-beep/ApexYX-Sovereign
    RUN_DATA=$(gh run list --limit 1 --repo xhall-beep/ApexYX-Sovereign --json status,conclusion)
    STATUS=$(echo $RUN_DATA | jq -r '.[0].status')
    if [ "$STATUS" == "completed" ]; then
        echo "✅ FORGE RESULT: $(echo $RUN_DATA | jq -r '.[0].conclusion')"
        break
    elif [ "$STATUS" == "in_progress" ]; then
        echo "⏳ The Cloud is hammering your Sovereignty into shape..."
    else
        echo "💤 Awaiting Action trigger..."
    fi
    sleep 10
done
