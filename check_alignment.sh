echo "🔱 SCANNING FOR 16KB ALIGNMENT COMPATIBILITY..."
find legacy_vault -name "*.so" | while read lib; do
    if readelf -l "$lib" 2>/dev/null | grep -q "LOAD" && readelf -l "$lib" 2>/dev/null | grep -q "0x4000"; then
        echo "✅ $lib is 16KB Aligned"
    else
        echo "⚠️ $lib needs Forge-Realignment"
    fi
done
