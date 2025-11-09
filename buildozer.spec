[app]
# App info
title = Benefit Buddy
package.name = BenefitBuddy
package.domain = mariosquirt.benefitbuddy
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,py3,csv,txt,gif,ttf,xml,json
version = 0.1

# Python & Kivy dependencies
requirements = python3,kivy==2.3.1,kivymd==1.2.0,requests,pandas,pillow,sqlite3,filetype,certifi,urllib3,chardet,idna

# Icons & Presplash
presplash.filename = %(source.dir)s/images/presplash.png
icon.filename = %(source.dir)s/images/icon.png

# Orientation
orientation = portrait

# Permissions
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# Fullscreen
fullscreen = 0
android.presplash_color = #005EA5

#
# Android settings
#
android.api = 34
android.minapi = 24
android.ndk_api = 24
android.archs = armeabi-v7a,arm64-v8a

# Explicitly set SDK and NDK paths (match GitHub Actions setup)
android.sdk_path = /home/runner/android-sdk
android.ndk_path = /home/runner/android-sdk/ndk/27.2.12479018

# Include your assets (fonts, images, etc.)
source.include_patterns = assets/*, data/*, font/*, images/*, images/loading/*, main.py, benefit_calculator.py, benefit_data/*, freedom.ttf, roboto.ttf

# Enable backup
android.allow_backup = True

# Debug/release artifacts
android.debug_artifact = apk
android.release_artifact = apk

#
# Python for Android
#
p4a.branch = master
p4a.bootstrap = sdl2

[buildozer]
log_level = 2
warn_on_root = 1
