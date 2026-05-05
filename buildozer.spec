[app]
title = TechSupport
package.name = techsupport
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,txt,json
version = 1.0
requirements = python3,kivy==2.2.1,requests==2.31.0,Pillow==10.1.0
orientation = portrait
fullscreen = 1
android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE
android.api = 30
android.minapi = 21
android.ndk = 23b
android.sdk = 30
android.arch = arm64-v8a