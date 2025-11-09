[app]
# App info
title = Benefit Buddy
package.name = BenefitBuddy
package.domain = mariosquirt.benefitbuddy
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,py3,csv,txt,gif,ttf,xml,json

version = 0.1

# Python & Kivy dependencies
# (Pinned to known-stable versions for Buildozer 1.5.0 / python-for-android 2024.10+)
requirements = python3,kivy==2.3.0,kivymd==1.1.1,requests,pandas,pillow,sqlite3,filetype,certifi,urllib3,chardet,idna

# Optional direct source for KivyMD to avoid GitHub rate-limiting
requirements.source.kivymd = https://github.com/kivymd/KivyMD/archive/refs/tags/1.1.1.zip

# Icons & Presplash
presplash.filename = %(source.dir)s/images/presplash.png
icon.filename = %(source.dir)s/images/icon.png
android.presplash_color = #005EA5

# Orientation
orientation = portrait

# Permissions
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# Fullscreen (0 = windowed, 1 = fullscreen)
fullscreen = 0

# Android settings
android.api = 34
android.minapi = 24
android.ndk_api = 24
android.archs = armeabi-v7a,arm64-v8a

# Assets and included files
source.include_patterns = assets/*, data/*, font/*, images/*, images/loading/*, main.py, benefit_calculator.py, benefit_data/*, freedom.ttf, roboto.ttf

# Allow backup (optional)
android.allow_backup = True

# Artifact format (APK only)
android.debug_artifact = apk
android.release_artifact = apk

# Python-for-Android settings
p4a.branch = stable
p4a.bootstrap = sdl2

[buildozer]
log_level = 2
warn_on_root = 1

# Optional: pin known-stable python-for-android in CI
# (do this in your GitHub Action before running buildozer)
# pip install "python-for-android==2024.10.1"
