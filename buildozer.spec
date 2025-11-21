[app]
title = Benefit Buddy
package.name = benefitbuddy
package.domain = org.benefitbuddy.app
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,ttf,otf
version = 1.0.0
requirements = python3,kivy,kivymd
orientation = portrait
fullscreen = 0

# Icons & Presplash
presplash.filename = %(source.dir)s/images/splash.png
icon.filename = %(source.dir)s/images/icon.png

android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.api = 34
android.minapi = 23
android.ndk = 25b
android.ndk_path = /home/runner/android-sdk/ndk/25.2.9519653
android.sdk_path = /home/runner/android-sdk
android.sdk_manager_path = /home/runner/android-sdk/cmdline-tools/latest/bin/sdkmanager
android.archs = arm64-v8a

android.gradle_dependencies = com.android.support:multidex:1.0.3


[buildozer]
log_level = 2
warn_on_root = 1
sdkmanager = /home/runner/android-sdk/cmdline-tools/latest/bin/sdkmanager
