[app]

# App Name
title = Benefit Buddy
package.name = BenefitBuddy
package.domain = mariosquirt.benefitbuddy

# Version
version = 0.1

# Source
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,py3,csv,txt,gif,ttf,xml,json

# Include all app assets
source.include_patterns = assets/*, data/*, font/*, images/*, images/loading/*, main.py, benefit_calculator.py, benefit_data/*, freedom.ttf, roboto.ttf

# Python + Kivy dependencies
requirements = python3==3.11.9, kivy==2.3.1, kivymd==1.2.0, requests, pandas, pillow, sqlite3, filetype, certifi, urllib3, chardet, idna

# P4A Recipes (whitelist only what CI must build)
android.recipe_whitelist = hostpython3,python3,kivy,kivymd,openssl,zlib,liblzma,freetype,jpeg,pillow,sqlite3,filetype,requests,certifi,idna,chardet,urllib3

# Orientation
orientation = portrait

# Permissions
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# Presplash and icons
presplash.filename = %(source.dir)s/images/presplash.png
icon.filename = %(source.dir)s/images/icon.png

fullscreen = 0
android.presplash_color = #005EA5

# Android API settings
android.api = 34
android.minapi = 24
android.ndk_api = 24
android.archs = armeabi-v7a,arm64-v8a

# FORCE Buildozer to use GitHub Actions SDK/NDK paths (Fix for sdkmanager problem)
android.sdk_path = $HOME/android-sdk
android.ndk_path = $HOME/android-sdk/ndk/25.2.9519653
android.ndk_version = 25b
android.sdk_manager_path = $HOME/android-sdk/cmdline-tools/latest/bin/sdkmanager

# Disable auto-download (CI provides SDK/NDK)
android.auto_sdk = 0
android.auto_ndk = 0

# Python for Android
p4a.branch = master
p4a.bootstrap = sdl2

# Enable caching
p4a.offline = 1

# Backup
android.allow_backup = True

# Artifact output
android.debug_artifact = apk
android.release_artifact = apk


[buildozer]

# IMPORTANT FIX: Point Buildozer to the modern location of sdkmanager
sdkmanager = $HOME/android-sdk/cmdline-tools/latest/bin/sdkmanager
