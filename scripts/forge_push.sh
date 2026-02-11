#!/bin/bash
cd ~/APEX_CORE
echo "🚀 [REECH] Injecting Diagnostic Uplink..."
git commit --allow-empty -m "🔱 V36.2: Log-Streamer Integration Engaged"
git push origin main --force

echo "📡 [MONITOR] Establishing Live Sovereign Log Stream..."
while true; do
    # Fetch the most recent Run ID
    RUN_ID=$(gh run list --limit 1 --repo xhall-beep/ApexYX-Sovereign --json databaseId -q '.[0].databaseId')
    
    if [ -z "$RUN_ID" ] || [ "$RUN_ID" == "null" ]; then
        clear
        echo "🔱 APEX SOVEREIGN LIVE MONITORING (V36.2)"
        echo "------------------------------------------------"
        echo "💤 Initializing Cloud Runner (Waiting for ID)..."
        sleep 10
        continue
    fi

    # Fetch Status
    STATUS=$(gh run view $RUN_ID --repo xhall-beep/ApexYX-Sovereign --json status -q '.status')
    
    clear
    echo "🔱 APEX SOVEREIGN LIVE MONITORING (V36.2)"
    echo "------------------------------------------------"
    echo "💎 RUN ID: $RUN_ID"
    echo "📡 STATUS: $STATUS"
    echo "------------------------------------------------"

    if [ "$STATUS" == "completed" ]; then
        CONCLUSION=$(gh run view $RUN_ID --repo xhall-beep/ApexYX-Sovereign --json conclusion -q '.conclusion')
        echo "✅ FORGE RESULT: $CONCLUSION"
        if [ "$CONCLUSION" == "failure" ]; then
            echo "🔍 CRITICAL ERROR DETECTED. STREAMING FAILURES:"
            gh run view $RUN_ID --log-failed --repo xhall-beep/ApexYX-Sovereign
        fi
        break
    elif [ "$STATUS" == "in_progress" ]; then
        echo "⏳ LIVE FORGE LOGS (Last 10 lines):"
        gh run view $RUN_ID --log --repo xhall-beep/ApexYX-Sovereign | tail -n 10
    fi
    sleep 15
done
