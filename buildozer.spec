[app]
title = APEX CORE
package.name = apexcore
package.domain = io.reech.sovereign
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,html,js,css,txt,sh,kts
version = 85.4

# Requirements for our agentic stack
requirements = python3,kivy==2.3.0,kivymd,flask,flask-socketio,eventlet,ptyprocess,requests,pandas,scikit-learn

orientation = portrait
fullscreen = 1
android.archs = arm64-v8a
android.allow_backup = False

# Android 16 / API 35 alignment
android.api = 35
android.gradle_dependencies = "org.jetbrains.kotlin:kotlin-stdlib:1.9.22"
android.gradle_dependencies = "org.jetbrains.kotlin:kotlin-stdlib:1.9.22"
android.minapi = 31
android.ndk = 28
android.ndk_path = 
android.sdk_path = 

# Permissions for Actual Factual Interaction
android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE, USB_PERMISSION, QUERY_ALL_PACKAGES

[buildozer]
log_level = 2
# Optimal Forge Parameters
android.skip_setup = False
android.copy_libs = 1
warn_on_root = 0
