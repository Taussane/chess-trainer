# Android app (Google Play)

A Trusted Web Activity: the app opens https://chessstrategy.org full screen (made with Bubblewrap, `twa-manifest.json`).
Package `org.chessstrategy.app`. The site proves it owns the app with `/.well-known/assetlinks.json` (the signing
keys' SHA-256 fingerprints: the upload key, and Play's app signing key from Play Console > App integrity).

Build (Android SDK 36, JDK 17+): `sdk.dir=…` in `local.properties`, then `./gradlew bundleRelease`, and sign
`app/build/outputs/bundle/release/app-release.aab` with the upload key (`jarsigner … upload`), which is never in
this repository. Each Play upload needs a higher `versionCode` (`app/build.gradle`, `twa-manifest.json`).
Changes from Bubblewrap's template: Maven Central at repo1.maven.org instead of jcenter; minSdk 24 (androidbrowserhelper).
