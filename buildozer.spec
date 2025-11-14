[app]
title = Benefit Buddy
package.name = BenefitBuddy
package.domain = mariosquirt.benefitbuddy

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,py3,csv,txt,gif,ttf,xml,json

# --- Python and Kivy stack ---
# MUST use a p4a-supported version → 3.11.4
requirements = python3==3.11.4, \
    kivy==2.3.1, \
    kivymd==1.2.0, \
    requests, \
    pandas, \
    pillow, \
    sqlite3, \
    filetype, \
    certifi, \
    urllib3, \
    chardet, \
    idna

# OPTIONAL but recommended: lock Python version
p4a.python_version = 3.11.4

# Recipes to ensure CI does not try downloading missing sources
android.recipe_whitelist = hostpython3,python3,kivy,kivymd,openssl,zlib,liblzma,freetype,jpeg,pillow,sqlite3,filetype,requests,certifi,idna,chardet,urllib3

version = 0.1

# --- UI Files ---
presplash.filename = %(source.dir)s/images/presplash.png
icon.filename = %(source.dir)s/images/icon.png

orientation = portrait
fullscreen = 0
android.presplash_color = #005EA5

# --- Permissions ---
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# --- Android Build Settings ---
android.api = 34
android.minapi = 24
android.ndk_api = 24
android.archs = armeabi-v7a,arm64-v8a

# --- SDK/NDK paths (for GitHub Actions CI) ---
android.sdk_path = /home/runner/android-sdk
android.ndk_path = /home/runner/android-sdk/ndk/25.2.9519653
android.ndk_version = 25.2.9519653
android.sdk_manager_path = /home/runner/android-sdk/cmdline-tools/latest/bin/sdkmanager

# Let CI install SDK/NDK instead of Buildozer
android.auto_sdk = 0
android.auto_ndk = 0

# Offline mode forces p4a to use cached downloads instead of remote URLs
p4a.offline = 1

# --- Bootstrap configuration ---
p4a.bootstrap = sdl2
p4a.branch = master

# --- Include Assets ---
source.include_patterns = \
    assets/*, \
    data/*, \
    font/*, \
    images/*, \
    images/loading/*, \
    main.py, \
    benefit_calculator.py, \
    benefit_data/*, \
    freedom.ttf, \
    roboto.ttf

android.allow_backup = True

# Debug/Release artifacts
android.debug_artifact = apk
android.release_artifact = apk
