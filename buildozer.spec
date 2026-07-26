[app]
title = Seed Blend Optimizer Pro
package.name = seedblendoptimizerpro
package.domain = org.seedblend
source.dir = .
source.include_exts = py,kv,json
source.exclude_dirs = tests,gui,__pycache__
source.main = kivy_app.py
version = 1.0.0
package.version_code = 1
requirements = python3,kivy,Pillow
orientation = portrait
fullscreen = 0
log_level = 2

[buildozer]
android.arch = arm64-v8a
android.api = 33
android.minapi = 21
android.ndk = 25c
android.permissions = 
p4a.branch = develop
android.gradle_dependencies = androidx.core:core:1.9.0

[app:android]
# Uncomment and set if you want a custom icon and launch image.
# icon.filename = %(source.dir)s/icon.png
# presplash.filename = %(source.dir)s/presplash.png
