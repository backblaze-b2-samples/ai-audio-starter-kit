<!-- last_verified: 2026-05-21 -->
# Feature: Audio Playback

## Purpose
Play uploaded audio assets directly from B2 in the browser, without proxying bytes through the API. The Library card swaps its action row for a native `<audio controls>` element fed by a short-lived presigned URL.

## Used By
- UI: `apps/web/src/components/library/audio-asset-card.tsx`
- API: `GET /library/{key}/playback`, `GET /library/{key}/download`

## Core Functions
- `services/api/app/runtime/library.py` — `/library/{key}/playback` and `/library/{key}/download` handlers
- `services/api/app/service/library.py::get_playback_url`, `get_download_url`
- `services/api/app/repo/b2_client.py::presign_audio_playback`, `get_presigned_url`
- `apps/web/src/lib/api-client.ts::getPlaybackUrl`, `getLibraryDownloadUrl`
- `apps/web/src/components/library/audio-asset-card.tsx::handlePlay` / `handleDownload`

## Canonical Files
- Presign pattern: `services/api/app/repo/b2_client.py`
- Playback UX: `apps/web/src/components/library/audio-asset-card.tsx`

## Inputs
- key: path param matching `^audio/[A-Za-z0-9_][A-Za-z0-9_./\-]*\.(wav|mp3|flac|ogg|m4a|aac|opus)$` (case-insensitive); `..` / `//` are rejected. Accepts both the Upload pipeline's `audio/<YYYY>/<MM>/<safe-filename>--<uuid>.<ext>` shape and externally-seeded audio under `audio/`.

## Outputs
- `GET /library/{key}/playback` -> `{ url: string, expires_in: 600 }` — presigned GET, no Content-Disposition (so the browser renders inline)
- `GET /library/{key}/download` -> `{ url: string, expires_in: 600 }` — presigned GET with `Content-Disposition: attachment; filename="..."` so the browser downloads instead of rendering

## Flow
- User clicks **Play** on an `AudioAssetCard`
- Card calls `getPlaybackUrl(key)` -> `/library/{key}/playback`
- Service validates the key against `AUDIO_KEY_RE`
- Service HEADs the object to confirm it exists -> 404 if not
- Repo mints a 10-minute presigned GET (no Content-Disposition)
- Card sets `audioSrc` and replaces the action row with `<audio controls src={audioSrc} autoPlay />`
- Browser fetches bytes directly from B2 — the API is not in the playback path

## Download flow
Identical to Playback, but the presigned URL is generated with `ResponseContentDisposition: attachment; filename="<basename>"` so the browser triggers a download instead of inline rendering. Audio downloads do **not** increment the `total_downloads` counter (that counter is scoped to the `/files/{key}/download` surface).

## Expiry and caching
- `expires_in: 600` (10 minutes). Long enough for a user to start playback; short enough that a stolen URL has limited blast radius.
- The browser will cache the audio bytes for the lifetime of the URL. After expiry the next play / scrub past a non-buffered region will fail; the user just clicks Play again to mint a fresh URL.
- TanStack Query does not cache the playback URL — every Play click mints a fresh one. (Each presigned URL is single-purpose and cheap to generate.)

## Edge Cases
- **Listed but missing object** -> 404 with detail "Audio asset not found"; the card toasts the error and remains in its pre-play state
- **Malformed key** -> 400 from the API before B2 is touched
- **B2 unreachable** -> 500; the card toasts a friendly error
- **Long file** -> handled by `<audio controls>` directly; no special server-side work

## UX States
- Pre-play: action row with Play / Download / Delete
- Loading: Play button shows "Loading..." while presigning
- Playing: inline `<audio controls>` with native browser scrubber
- Error: toast surfaces the failure; the action row remains visible

## Verification
- Test files: extend `services/api/tests/` with playback / download URL flow coverage — not shipped in the scaffold
- Quick verify command: `pnpm test:api`
- Pass criteria: all pytest tests green

## Related Docs
- [Audio Library](audio-library.md)
- [Audio Upload](file-upload.md)
- [ARCHITECTURE.md](../../ARCHITECTURE.md)
