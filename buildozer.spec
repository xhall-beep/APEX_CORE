[app]
android.gradle_dependencies = sqlite3, libffi
title = APEX CORE
package.name = apexcore
package.domain = org.svontz
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 2.0.5

# 🔱 Optimized Requirements
requirements = python3,hostpython3,kivy==2.2.1,cython==0.29.33,certifi,openssl,libffi,sqlite3

orientation = portrait
osx.python_version = 3
osx.kivy_version = 2.3.0
fullscreen = 0

# 🔱 Android Sovereign Forge Settings
android.api = 33
android.sdk = 34
android.ndk = 25b
android.ndk_api = 21
android.archs = arm64-v8a
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 0
