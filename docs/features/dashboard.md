<!-- last_verified: 2026-05-21 -->
# Feature: Dashboard

## Purpose
Audio-aware overview of B2 storage activity: total audio assets, total duration, recent uploads, and a 7-day activity chart.

## Used By
- UI: `/` page (dashboard home)
- API: `GET /files/stats`, `GET /files`, `GET /files/stats/activity`

## Core Functions
- `apps/web/src/components/dashboard/stats-cards.tsx` — 4 stat cards: Audio Assets, Total Duration, Uploads Today, Total Downloads
- `apps/web/src/components/dashboard/recent-uploads-table.tsx` — last 10 uploads (audio + generic)
- `apps/web/src/components/dashboard/upload-chart.tsx` — bar chart of uploads per day
- `apps/web/src/lib/api-client.ts` — `getFileStats()`, `getFiles()`, `getUploadActivity()`
- `services/api/app/runtime/files.py` — `GET /files/stats` handler
- `services/api/app/service/files.py` — `get_stats()` merges the generic `get_upload_stats()` with `get_audio_aggregates()`
- `services/api/app/service/library.py` — `get_audio_aggregates()` totals the `audio/` prefix
- `services/api/app/repo/b2_client.py` — `get_upload_stats()`, `list_audio_objects()`

## Canonical Files
- Dashboard page layout: `apps/web/src/components/dashboard/stats-cards.tsx`
- Stats service logic: `services/api/app/service/files.py`

## Inputs
- None (dashboard loads data automatically)

## Outputs
- `GET /files/stats` -> `UploadStats` (`total_files`, `total_size_bytes`, `total_size_human`, `uploads_today`, `total_downloads`, `total_audio_assets`, `total_duration_ms`)
- `GET /files` (limit 10) -> `FileMetadata[]` for recent uploads table (sorted newest-first)
- `GET /files/stats/activity?days=7` -> `DailyUploadCount[]` for chart (server-side aggregation)

## Flow
- Page loads -> three parallel API calls (stats, recent files, upload activity)
- Stats cards display: Audio Assets, Total Duration (formatted `m:ss` / `h:mm:ss`), Uploads Today, Total Downloads
- Upload chart displays server-aggregated daily counts for last 7 days as bar chart
- Recent uploads table shows last 10 files with filename, size, type, date, status badge

## Notes on `total_duration_ms`
The scaffold currently reports `0` for `total_duration_ms`. Per-asset duration is extracted at upload time and returned in the `FileUploadResponse`, but the Library list endpoint does not currently HEAD every object to read it back (that would turn a single S3 call into N+1). Downstream samples that need a real total can either persist `duration_ms` as S3 object metadata at upload time, or store an out-of-band index. The dashboard tile reads `total_duration_ms` so the wire-up is ready as soon as the field is populated.

## Edge Cases
- API unavailable -> stats default to zeros, table shows empty state
- B2 stats aggregation fails -> `/files/stats` returns 500 with `Failed to load file stats`
- B2 activity aggregation fails -> `/files/stats/activity` returns 500 with `Failed to load upload activity`
- No files uploaded -> empty chart message, empty table message
- Large file count -> stats endpoint paginates through all objects using `ContinuationToken`

## UX States
- Loading: skeleton placeholders for cards and table
- Empty: "No uploads yet" / "No activity yet"
- Loaded: populated cards, chart, table

## Verification
- Test files: `services/api/tests/test_upload_activity.py`, `services/api/tests/test_recent_files.py`, `services/api/tests/test_download_stats.py`
- Required cases: stats with files, stats with empty bucket, API error fallback
- Quick verify command: `pnpm test:api`
- Full verify command: `pnpm lint && pnpm lint:api && pnpm test:api && pnpm check:structure`
- Pass criteria: all pytest tests green, no ruff violations

## Related Docs
- [ARCHITECTURE.md](../../ARCHITECTURE.md)
- [App Workflows](../app-workflows.md)
