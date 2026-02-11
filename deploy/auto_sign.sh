#!/bin/bash
# Search for the newly minted APK in the buildozer directory
APK_PATH=$(find $HOME/APEX_CORE/.buildozer/android/platform/build-arm64-v8a/dists/ -name "*.apk" | head -n 1)
if [ -n "$APK_PATH" ] && [ -f "$APK_PATH" ]; then
    echo "🔱 APEX CORE DETECTED: COMMENCING SOVEREIGN SIGNING..."
    cp "$APK_PATH" $HOME/APEX_CORE/deploy/apex_unsigned.apk
    apksigner debug $HOME/APEX_CORE/deploy/apex_unsigned.apk $HOME/APEX_CORE/deploy/APEX_V600_READY.apk
    mv $HOME/APEX_CORE/deploy/APEX_V600_READY.apk /sdcard/Download/
    echo "✅ SUCCESS: APEX_V600_READY.apk is now in your phone's Download folder."
else
    echo "⏳ Awaiting build completion..."
fi
