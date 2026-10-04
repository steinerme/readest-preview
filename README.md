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

PDFs default to text reflow once the original reader has restored its location. The top toolbar offers **Switch to PDF**, and the original view offers a direct **Switch to Reflow** button. A manual switch stays in the original view for that reader session. This is a local, page-based reading mode for upright single-column PDFs with text layers. It supports adjustable font size/line spacing, small notes, original physical page navigation, and return to the original view. It does not do OCR, reconstruct formulas, create synthetic annotations, or convert the entire PDF into a new book. Tables and figures are handled as described in the 20016 section below. Reflow renders inside the original reader content layer: tap text to show the same HeaderBar/FooterBar; only the mode-switch label reverses. Original TOC, bookmark, notebook, settings, brightness/theme, progress/page-jump, and read-aloud services remain available. Font/spacing come from the same saved ViewSettings. Android Back uses the original reader hierarchy and shared dialogs. Original annotations are mapped to reflow text through proven original text-layer Range/CFI anchors, never synthetic locations; ambiguous source mappings disable position-dependent tools rather than saving wrong notes. Page is remembered within the app session; text caches remain panel-local. Full details and test boundaries are in the patched `docs/pdf-reflow.md`.

Reflow now exposes the existing read-aloud transport, highlights real spoken word/sentence ranges, scrolls to the active range and follows physical page changes. Manual scrolling/page navigation suspends visual following; Return to Current Speech resumes it. Switching to the original PDF does not stop audio. Range provenance is mapped from the original PDF item stream, not guessed from repeated sentence text. Engines without word boundaries use sentence highlighting; transformed/mismatched text refuses uncertain highlights. Listening still follows the original PDF text-layer order, so complex visual layouts remain unsupported.

The post-20005 fix verifies PDF navigation using fixed-layout's actual physical `index`, rather than its nonexistent `primaryIndex`, and places listening/page controls in a separate flow-layout footer. The scrollable article receives only the remaining height: footer wrapping on narrow screens never overlays body text. 315 targeted tests and the project typecheck pass locally; real WebView CSS checks cover phone/narrow/landscape dimensions, but the updated APK still needs device acceptance. An intermittent visual-follow detachment observed in the prior device test is not addressed by these two fixes.

The post-20006 update unifies read-aloud UI: reflow borrows the original mini player and full player sheet through a per-book visual host, while the same mounted TTSControl keeps ownership of the playback session. It exposes speed, voice, timeout, sentence navigation, and timeline seeking when supported by the engine. The card occupies real footer height and remains reachable with reflow chrome hidden; Back/Escape dismiss the nested player before leaving the reader. 21 targeted files / 392 tests and the full TypeScript check pass locally. A broader compatible set passes 50 files / 731 tests; three unrelated cache suites cannot load Turso native bindings in the local Alpine environment. No updated APK device acceptance is claimed.

The post-20007 update replaces the separate reflow overlay/chrome with inline reader content and reuses the actual original header/footer components and services. 27 build-gate files / 428 tests and the full TypeScript check pass locally; a broader 43-file run passed 574 tests before the final bookmark/selection additions. Real reflow CSS with representative original bars was checked at phone/narrow/landscape sizes across 18 states, including expanded panels with an active mini player. These fixtures are not APK device acceptance. PDF-wide translation remains unavailable exactly as in the original; page-image-specific layout options do not create new reflow capabilities.

The user's sample PDFs and extracted text are never published here. The existing preview signing key is reused for in-place preview updates.

## Scope

This is an initial bookshelf/reader-controls/dialog polish, not a full WeChat Read-level redesign. UI regression tests passed in the development environment, but a successful APK build is not equivalent to device usability or performance verification.
Do not uninstall the official app. Start with disposable local test books; independent app data does not automatically import your existing library.

## 20016: launch splash icon, tables and figures in reflow

- The window-background splash (visible when switching back from another app) and the media-notification small icon were still upstream's open-book artwork. `prepare_preview.py` now replaces both from the private branding artwork, and `verify_apk_branding.py` fails the build if the final APK lacks them or still packages the upstream bitmap.
- Reflow now reads each page's operator list (read-only) to find bitmaps, ruling lines and vector shapes. Ruled grids, three-rule tables and rule-less aligned tables become real `<table>` elements with header cells and numeric alignment; each cell is a reflow block so speech highlight, selection and citations keep working. Bitmaps and dense vector drawings become lazily rendered figure images, and their axis/legend labels no longer pollute the text flow. Any extraction failure falls back to the previous text-only reflow.
- Still unsupported: multi-column reading order (flagged as before), rotated pages, formulas, OCR, and listening to figures.

## Reading AI (20020)
See `docs/reading-ai.md` (inside `reading-polish.patch`). Floating round **Listen** and **AI** buttons sit on the reading page and hide whenever the tap-to-show bars, a side panel, settings or any sheet/dialog/popup is open. Retrieval is now BM25 with neighbouring paragraphs and an optional cloud step that sends only the question to suggest extra search words. Confirmation can be skipped per book/range for the current session (never for whole-book scope), follow-ups are budgeted by size, answers are kept in a local per-book history, and re-opening a book after a break shows a "where you left off" card with a recap shortcut. OCR is not included.
