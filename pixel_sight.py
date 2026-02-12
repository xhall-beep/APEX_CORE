import os
import subprocess

def capture_screen():
    print("🔱 APEX SIGHT: CAPTURING PIXEL 8 PRO SCREEN...")
    # This assumes ADB is connected via wireless debugging or USB
    try:
        os.system("adb shell screencap -p /sdcard/screen.png")
        os.system("adb pull /sdcard/screen.png ./deliveries/screen.png")
        return "🔱 SCREEN CAPTURED: Viewable in Command Center."
    except Exception as e:
        return f"⚠️ SIGHT ERROR: {str(e)}"

if __name__ == "__main__":
    print(capture_screen())
