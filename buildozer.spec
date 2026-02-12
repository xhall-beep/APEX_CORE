[app]
title = APEX CORE
package.name = apexcore
package.domain = org.svontz
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 2.0.5

# 🔱 Optimized Requirements
requirements = python3,kivy==2.3.0,six,pyjnius,sqlite3

orientation = portrait
osx.python_version = 3
osx.kivy_version = 2.3.0
fullscreen = 0

# 🔱 Android Sovereign Forge Settings
android.api = 34
android.sdk = 34
android.ndk = 25b
android.ndk_api = 21
android.archs = arm64-v8a
android.allow_backup = True
android.gradle_dependencies = sqlite-jdbc:3.34.0

[buildozer]
log_level = 2
warn_on_root = 0
