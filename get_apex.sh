#!/bin/bash
TARGET_REPO="xhall-beep/APEX_CORE"
echo "📡 Reech is standing by for the Golden APK..."

while true; do
    RESULT=$(gh run list --limit 1 --repo "$TARGET_REPO" --json status,conclusion -q '.[0] | "\(.status) \(.conclusion)"')
    if [[ "$RESULT" == "completed success" ]]; then
        echo "🔱 SUCCESS DETECTED. DOWNLOADING SOVEREIGN APK..."
        gh run download $(gh run list --limit 1 --repo "$TARGET_REPO" --json databaseId -q '.[0].databaseId') --name "bin" --dir ./build_output
        echo "✅ DOWNLOAD COMPLETE: Check ~/APEX_CORE/build_output"
        break
    elif [[ "$RESULT" == *"failure"* ]]; then
        echo "⚠️  FORGE FAILURE. ANALYZING IN SESSION 2..."
        break
    fi
    sleep 15
done
