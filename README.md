# Readest Preview (unofficial)

Personal Android UI preview of [Readest](https://github.com/readest/readest), not an official release.

## Reproducible source

- Upstream commit: `6e567ef3106a9bf6e6daa697760db66cc30b4b8a` (Readest 0.12.10).
- `reading-polish.patch` contains every UI modification, tests, and detailed validation notes.
- `foliate-reflow.patch` adds a read-only PDF text extraction API to the pinned foliate-js submodule; the workflow applies it after initializing submodules.
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

## PDF text reflow (new)

PDFs default to text reflow once the original reader has restored its location. The top toolbar offers **Switch to PDF**, and the original view offers a direct **Switch to Reflow** button. A manual switch stays in the original view for that reader session. This is a local, page-based reading mode for upright single-column PDFs with text layers. It supports adjustable font size/line spacing, small notes, original physical page navigation, and return to the original view. It does not do OCR, reconstruct images/formulas/tables, create synthetic annotations, or convert the entire PDF into a new book. Reflow opens in immersive reading mode: tap text or the corner page button to reveal controls; Aa opens dismissible settings. Android Back dismisses settings first, otherwise returns directly to the library without waiting for PDF rendering. The separate original-page action also closes immediately before requesting navigation. Page/font/spacing are remembered per book within the app session; text caches remain panel-local. Full details and test boundaries are in the patched `docs/pdf-reflow.md`.

Reflow now exposes the existing read-aloud transport, highlights real spoken word/sentence ranges, scrolls to the active range and follows physical page changes. Manual scrolling/page navigation suspends visual following; Return to Current Speech resumes it. Switching to the original PDF does not stop audio. Range provenance is mapped from the original PDF item stream, not guessed from repeated sentence text. Engines without word boundaries use sentence highlighting; transformed/mismatched text refuses uncertain highlights. Listening still follows the original PDF text-layer order, so complex visual layouts remain unsupported.

The post-20005 fix verifies PDF navigation using fixed-layout's actual physical `index`, rather than its nonexistent `primaryIndex`, and places listening/page controls in a separate flow-layout footer. The scrollable article receives only the remaining height: footer wrapping on narrow screens never overlays body text. 315 targeted tests and the project typecheck pass locally; real WebView CSS checks cover phone/narrow/landscape dimensions, but the updated APK still needs device acceptance. An intermittent visual-follow detachment observed in the prior device test is not addressed by these two fixes.

The post-20006 update unifies read-aloud UI: reflow borrows the original mini player and full player sheet through a per-book visual host, while the same mounted TTSControl keeps ownership of the playback session. It exposes speed, voice, timeout, sentence navigation, and timeline seeking when supported by the engine. The card occupies real footer height and remains reachable with reflow chrome hidden; Back/Escape dismiss the nested player before leaving the reader. 21 targeted files / 392 tests and the full TypeScript check pass locally. A broader compatible set passes 50 files / 731 tests; three unrelated cache suites cannot load Turso native bindings in the local Alpine environment. No updated APK device acceptance is claimed.

The user's sample PDFs and extracted text are never published here. The existing preview signing key is reused for in-place preview updates.

## Scope

This is an initial bookshelf/reader-controls/dialog polish, not a full WeChat Read-level redesign. UI regression tests passed in the development environment, but a successful APK build is not equivalent to device usability or performance verification.
Do not uninstall the official app. Start with disposable local test books; independent app data does not automatically import your existing library.
