[app]
title = Benefit Buddy
package.name = benefitbuddy
package.domain = org.mariosquirt
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0
requirements = kivy
orientation = portrait
osx.python_version = 3
osx.kivy_version = 2.2.1
fullscreen = 1
icon.filename = %(source.dir)s/icon.png
presplash.filename = %(source.dir)s/presplash.png

[buildozer]
log_level = 2
warn_on_root = 1

[python]
# Add any Python files or packages your app needs

[android]
minapi = 21
sdk = 34
android.permissions = INTERNET,ACCESS_NETWORK_STATE, ACCESS_FINE_LOCATION

android.ndk = 23b

[ios]
# ios.kivy_ios_url = https://github.com/kivy/kivy-ios
# ios.kivy_ios_branch = master

[window]
# window.size = 800,600
