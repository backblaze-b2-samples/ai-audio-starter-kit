<!-- last_verified: 2026-05-22 -->
# Feature: Audio Library

## Purpose
List, play back, download, and delete every audio asset the user has stored
in B2 — sourced entirely from S3 list/head/delete so there is no
application database. Scoped to the `audio/` prefix; the full bucket lives
at `/files`.

## Used By
- UI: `/library` page
- API:
  - `GET /library`
  - `GET /library/{key}/playback`
  - `GET /library/{key}/download`
  - `DELETE /library/{key}`
  - `POST /library/bulk-delete`

## Core Functions
- `apps/web/src/components/library/library-view.tsx` — responsive grid of cards (`sm:grid-cols-2 xl:grid-cols-3`), Refresh button, skeletons, EmptyState, ErrorState, multi-select header (select-all checkbox + "N selected" + Delete) and bulk-delete confirm dialog
- `apps/web/src/components/library/audio-asset-card.tsx` — individual card: optional selection checkbox (highlights with `ring-2 ring-primary` when selected), title preview, metadata strip, inline `<Waveform />`, Play / Download / Delete (AlertDialog confirm), inline `<audio controls>` on Play
- `apps/web/src/components/library/waveform.tsx` — lightweight SVG waveform (duration-keyed stub by default, downsampled-peak rendering when samples are available)
- `apps/web/src/lib/queries.ts::useLibrary`, `useDeleteAudioAsset`, `useBulkDeleteAudioAssets`
- `apps/web/src/lib/api-client.ts::getLibrary`, `getPlaybackUrl`, `getLibraryDownloadUrl`, `deleteAudioAsset`, `bulkDeleteAudioAssets`
- `services/api/app/runtime/library.py` — FastAPI routes
- `services/api/app/service/library.py` — key validation, listing, delete, bulk delete, aggregates
- `services/api/app/repo/b2_audio.py::list_audio_objects`, `head_audio_object`, `head_audio_objects_parallel`, `delete_audio_object`, `delete_audio_objects_batch`, `presign_audio_playback`

## Canonical Files
- Pattern exemplar: `apps/web/src/components/library/audio-asset-card.tsx`
- Service orchestration: `services/api/app/service/library.py`

## Inputs
- limit: int (query param on `GET /library`, default 100, max 500)
- key: path param on `/library/{key}/...` — must match `^audio/[A-Za-z0-9_][A-Za-z0-9_./\-]*\.(wav|mp3|flac|ogg|m4a|aac|opus)$` (case-insensitive) and contain no `..` or `//`. Canonical shape from Upload is `audio/<YYYY>/<MM>/<safe-filename>--<uuid>.<ext>`, but any audio file under `audio/` is accepted.
- `POST /library/bulk-delete` body: `{ keys: string[] }` (1-1000 keys, each matching the same regex above)

## Outputs
- `GET /library` -> `AudioAsset[]` sorted newest-first (key, size, content_type, created_at, duration_ms, sample_rate, channels, bit_depth, codec, title_preview)
- `GET /library/{key}/playback` -> `{ url, expires_in }` — inline presigned GET (no Content-Disposition)
- `GET /library/{key}/download` -> `{ url, expires_in }` — presigned GET with `Content-Disposition: attachment`
- `DELETE /library/{key}` -> `{ deleted: true, key }`
- `POST /library/bulk-delete` -> `{ deleted: string[], errors: { Key, Code, Message }[] }` — partial success is allowed and surfaced to the UI
- Side effect on delete or bulk-delete: TanStack Query invalidates library + stats

## Flow
- `GET /library` -> `list_objects_v2(Prefix="audio/")` -> sort newest-first -> fan out HEADs via `head_audio_objects_parallel` (default 10 workers, capped at `limit`) to pull `duration_ms`, `sample_rate`, `channels`, `bit_depth`, `codec` out of the `x-amz-meta-*` user metadata stamped at upload time -> return
- Playback / download -> validate the key against the regex -> HEAD for existence -> mint a presigned GET (with the right `ResponseContentDisposition` for download) -> return URL
- Delete -> validate key -> `delete_object` -> 200
- Bulk delete -> validate every key (regex + no `..`/`//`) before any B2 call -> deduplicate -> one S3 `DeleteObjects` call (chunks of 1000) -> return `{ deleted, errors }`. Mixed partial failures show a "Deleted N of M — K failed" toast.

## Notes on list metadata
- Externally-seeded files (objects under `audio/` that didn't go through the Upload pipeline) have no `x-amz-meta-*` block; their audio fields stay `None` and the asset card falls back to extension-derived `codec`. They are still listed, played, and counted in the dashboard's `total_audio_assets` and `formats`.
- The dashboard's `get_audio_aggregates()` sums real `total_duration_ms` from the same `x-amz-meta-duration-ms` field — there is no longer a placeholder `0` total duration on the dashboard.

## Edge Cases
- **Listed-but-not-head-able key** -> playback / download return 404 (transient B2 consistency artifact); the rest of the library still renders
- **Malformed key** -> 400 from the API before B2 is touched
- **Missing key** -> 404 with the canonical "Audio asset not found" body
- **B2 unreachable** -> 500 with `Internal server error`; raw error is not leaked
- **Empty prefix** -> 200 with `[]`; the UI shows the empty state

## UX States
- Loading: 6 skeleton cards
- Empty: friendly `EmptyState` — "Nothing here yet — upload an audio file to get started"
- Loaded: responsive grid of `AudioAssetCard`s
- Error: `ErrorState` with retry

## Verification
- Test files: `services/api/tests/test_bulk_delete.py` (library half — happy path, non-audio prefix rejection, path-traversal rejection, partial errors). Single-asset playback / delete / list flows not covered in the scaffold beyond structural tests.
- Quick verify command: `pnpm test:api`
- Full verify command: `pnpm lint && pnpm lint:api && pnpm test:api && pnpm check:structure`
- Pass criteria: all pytest tests green, no ruff violations

## Related Docs
- [Audio Upload](file-upload.md)
- [Audio Playback](audio-playback.md)
- [Audio Metadata Extraction](audio-metadata.md)
- [ARCHITECTURE.md](../../ARCHITECTURE.md)
- [App Workflows](../app-workflows.md)
