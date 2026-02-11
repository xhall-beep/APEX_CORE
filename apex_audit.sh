#!/data/data/com.termux/files/usr/bin/bash
echo "🔱 [REECH_AUDIT] - Scanning Sovereign Environment..."
ERRORS=0

# Check 1: NDK Path Check
if [[ "$CLANG_PATH" == *"x86_64"* ]]; then
    echo "❌ ERROR: Path Hallucination! System is looking for x86_64 binaries."
    ((ERRORS++))
fi

# Check 2: Native Compiler Check
if ! command -v clang &> /dev/null; then
    echo "❌ ERROR: Clang not found in native path."
    ((ERRORS++))
fi

# Check 3: API Target Check
if [ ! -d "/home/.buildozer/android/platform/android-sdk/platforms/android-31" ]; then
    echo "❌ ERROR: API 31 (Android 12) is missing from SDK."
    ((ERRORS++))
fi

if [ $ERRORS -gt 0 ]; then
    echo "⚠️  Found $ERRORS issues. Applying Sovereign Multi-Bridge fixes..."
    export CC=clang
    export CXX=clang++
    export CLANG_PATH=$PREFIX/lib/android-ndk/toolchains/llvm/prebuilt/linux-aarch64/bin
    export ANDROID_NDK_HOME=$PREFIX/lib/android-ndk
    export PATH=$CLANG_PATH:$PATH
    echo "✅ Fixes applied. Try running 'buildozer -v android debug' now."
else
    echo "💎 Status: OPTIMAL. All systems go."
fi
