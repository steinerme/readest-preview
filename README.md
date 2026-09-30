# Readest Preview (unofficial)

Personal Android UI preview of [Readest](https://github.com/readest/readest), not an official release.

## Reproducible source

- Upstream commit: `6e567ef3106a9bf6e6daa697760db66cc30b4b8a` (Readest 0.12.10).
- `reading-polish.patch` contains every UI modification, tests, and detailed validation notes.
- `prepare_preview.py` contains all Android packaging changes.
- The workflow checks out that exact commit, applies the patch and builds an ARM64 APK.
- Source and modifications remain under AGPL-3.0; see LICENSE and upstream notices.

## Install isolation

Android application ID: `com.bilingify.readest.preview`; launcher label: **Readest Preview**.
The Kotlin namespace is preserved for Tauri JNI compatibility. Android app identity, provider authority and private data are separate from the official app.
Official OAuth and HTTPS app-link handlers are removed from the preview manifest to avoid intercepting the official app's callbacks. Use local test books; do not use this preview for purchases or assume cloud authentication works.

## Build and download

Actions → **Build Readest Preview APK** → Run workflow. Download artifact **Readest-Preview-arm64** when successful and extract its APK. No APK exists until a build succeeds.
Signing requires repository Secrets `PREVIEW_KEYSTORE` (base64 JKS) and `PREVIEW_KEY_PASSWORD`, alias `preview`. They are private and never part of this repository. Keep the same signing key to update this preview without reinstalling.

The workflow uses standard public GitHub-hosted runners, not paid larger runners. No scheduled, push or PR builds are enabled.

## Scope

This is an initial bookshelf/reader-controls/dialog polish, not a full WeChat Read-level redesign. UI regression tests passed in the development environment, but a successful APK build is not equivalent to device usability or performance verification.
Do not uninstall the official app. Start with disposable local test books; independent app data does not automatically import your existing library.
