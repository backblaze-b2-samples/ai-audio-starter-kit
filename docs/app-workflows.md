<!-- last_verified: 2026-05-21 -->
# App Workflows

User journeys inside the application.

## Upload Audio

- User navigates to `/upload`
- Drops or selects audio files in the dropzone
- Client validates file size (max 100MB) and type
- Progress bar shows per-file upload status
- API validates the MIME (`audio/*`), sanitizes the filename, and writes to B2 under `audio/<YYYY>/<MM>/<safe-filename>--<uuid>.<ext>` — the UUID guarantees collision-free keys while the embedded filename surfaces in Library cards and download Content-Disposition
- Server-side audio metadata extraction (`.wav` via stdlib `wave`, everything else via `mutagen`) returns duration / sample rate / channels / bit depth / codec
- On success: toast notification, green checkmark; the asset is now visible in `/library`
- On failure: red status icon with error message
- Non-audio uploads are still accepted (for parity with the underlying starter) and land under the `uploads/` prefix — they only show in Files, not in Library
- See: [Audio Upload](features/file-upload.md), [Audio Metadata Extraction](features/audio-metadata.md)

## Browse the Audio Library

- User navigates to `/library`
- Page loads the asset list from `GET /library` (sorted newest-first)
- Each `AudioAssetCard` shows: filename, duration · sample rate · channels · created date, an inline waveform stub, and Play / Download / Delete actions
- **Play**: fetches a short-lived presigned URL via `GET /library/{key}/playback` and renders an inline `<audio controls>` element
- **Download**: fetches a presigned URL via `GET /library/{key}/download` (with `Content-Disposition: attachment`), opens in a new tab
- **Delete**: AlertDialog confirms; on accept, `DELETE /library/{key}` removes the asset, TanStack Query invalidates the library + stats caches
- **Bulk delete**: per-card checkbox + header select-all toggle to select multiple assets; an action bar shows "N selected" with Clear and Delete; confirm dialog -> `POST /library/bulk-delete` -> toast reports full / partial / total failure
- Empty bucket shows "Nothing here yet — upload an audio file to get started"
- See: [Audio Library](features/audio-library.md), [Audio Playback](features/audio-playback.md)

## Browse the Full Bucket (Files)

- User navigates to `/files`
- Page loads file list from `GET /files` (sorted most recent first)
- Files displayed in tree view with folders and type-specific icons
- Top-level folders auto-expand on load (so `audio/` and `uploads/` are immediately visible)
- Hover a file row to see action buttons (preview / download / delete)
- **Preview**: opens dialog with image/PDF preview + metadata panel for non-audio content
- **Download**: fetches presigned URL, browser downloads file
- **Delete**: removes file from B2, row removed from tree, toast confirms
- **Bulk delete**: per-row and per-folder checkboxes (folder shows an indeterminate state when only some descendants are selected) — select files and use the header **Delete** to `POST /files/bulk-delete`; toast reports full / partial / total failure
- Empty bucket shows "This bucket is empty" with upload prompt
- See: [Bucket Explorer](features/file-browser.md)

## View Dashboard

- User navigates to `/` (home)
- Header offers two actions: a primary **Upload audio** CTA and a secondary **Browse library** link
- Empty state: when the bucket holds no audio, the page collapses to a single hero card ("No audio yet — upload your first track") with the upload CTA. The grid below is hidden until the first asset lands
- With audio present, the dashboard loads in parallel: stats, recent audio uploads, upload activity
- **Stats tiles**: total audio assets, total duration, uploads today, and **Audio Storage** (total bytes used by the `audio/` prefix, humanized)
- **Format breakdown card**: compact chips showing per-extension counts (e.g. `wav 5 · mp3 12 · flac 1`), sorted by count desc; hidden when the bucket holds no recognized formats
- **Upload activity chart**: last 7 days as a bar chart, with a segmented **Uploads / Minutes** toggle — "Uploads" plots the per-day asset count, "Minutes" plots minutes of audio added per day. The chart and the "Total" number in the header switch together
- **Recent audio uploads table**: last 10 audio assets with columns **Filename / Duration / Format / Date / ▶ Play**. The Play action opens a small dialog with an inline `<audio controls autoPlay>` element backed by a presigned URL. "View all" links to `/library`
- See: [Dashboard](features/dashboard.md)
