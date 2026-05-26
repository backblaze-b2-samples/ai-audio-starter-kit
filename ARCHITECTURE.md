<!-- last_verified: 2026-05-21 -->
# Architecture

## Components

- **apps/web/** — Next.js 16 frontend (App Router, Tailwind v4, shadcn/ui)
  - Dashboard with audio-aware stats (total audio assets, total duration), upload activity chart, recent uploads table
  - Audio **Library** (`/library`) — `AudioAssetCard` grid scoped to the `audio/` prefix, inline `<audio>` playback, waveform stub, download, delete
  - Audio **Upload** (`/upload`) — drag-and-drop with progress tracking; audio uploads land under `audio/<YYYY>/<MM>/<safe-filename>--<uuid>.<ext>`
  - **Files** (`/files`) — full B2 bucket explorer (tree view, preview, download, delete) for everything else
  - Dark mode via `next-themes`
- **services/api/** — FastAPI backend (layered architecture)
  - REST API for audio library, upload, listing, deletion
  - B2 S3 integration via boto3
  - Audio metadata extraction (`.wav` via stdlib `wave`, everything else via `mutagen` — no ffmpeg)
  - Health check endpoint with B2 connectivity verification
  - Structured JSON logging with request tracing
  - Prometheus-format metrics endpoint
- **packages/shared/** — TypeScript type definitions
  - Mirrors Pydantic models from the API (`FileMetadata`, `AudioAsset`, `UploadStats`, …)
  - Consumed by `apps/web/` as workspace dependency

## Backend Layering

The API follows a strict layered architecture:

```
types/     Pydantic models — no logic, no imports from other layers
  |
config/    Settings (pydantic-settings) — depends only on types
  |
repo/      Data access (boto3 B2 client) — no business logic
  |
service/   Business logic — calls repo, returns types
  |
runtime/   FastAPI routes — calls service, never repo directly
```

### Layering Rules

1. Dependencies flow downward only: `types` -> `config` -> `repo` -> `service` -> `runtime`
2. No backward imports (e.g., service must not import from runtime)
3. `boto3` only allowed in `repo/` layer
4. All boundary data uses Pydantic models (no raw dicts across layers)
5. Each file stays under 300 lines

### Directory Structure

```
services/api/
  main.py                  App entrypoint, middleware, router registration
  app/
    types/                 Pydantic models (FileMetadata, AudioAsset, UploadStats, …)
    config/                Settings loaded from environment
    repo/                  B2 S3 client — `b2_client.py` (generic file helpers) + `b2_audio.py` (audio-prefix helpers, incl. `head_audio_objects_parallel`)
    service/               Business logic — upload, files, library, audio_metadata
    runtime/               FastAPI route handlers — health, upload, files, library, metrics
  tests/                   pytest tests (structural + integration)
```

## Boundary Invariants

- **No external SDK leakage**: `boto3` is only imported in `app/repo/`. All other layers interact with B2 through the repo interface.
- **No raw dicts at boundaries**: All data crossing layer boundaries uses typed Pydantic models.
- **No mutable globals**: Configuration is read-only after init. No module-level mutable state shared between layers.
- **Validated inputs**: All HTTP inputs validated by FastAPI/Pydantic. Audio asset keys validated against `^audio/[A-Za-z0-9_][A-Za-z0-9_./\-]*\.(wav|mp3|flac|ogg|m4a|aac|opus)$` (case-insensitive) with explicit `..` / `//` rejection before any B2 call. The pattern accepts both the Upload pipeline's canonical `audio/<YYYY>/<MM>/<safe-filename>--<uuid>.<ext>` shape and externally-seeded audio under `audio/`.
- **Custom user agent**: every `boto3.client("s3", …)` sets `Config(user_agent_extra="b2ai-ai-audio-starter-kit")`. No `b2-native` calls.

## Deployment

- **Local dev** — `pnpm dev` runs both services via `concurrently`
  - Web: `localhost:3000`
  - API: `localhost:8000`
- **Railway** — two services from the same repo
  - See `infra/railway/README.md` for configuration

## Data Stores

- **Backblaze B2** — object storage (S3-compatible API)
  - Audio assets under the `audio/` prefix; the Library lists this prefix
  - Generic uploads under the `uploads/` prefix; only shown in the Files explorer
  - File listing and metadata via S3 `list_objects_v2` / `head_object`
  - No application database — B2 is the sole data store

## External Services

- **Backblaze B2 S3 API** — audio storage, retrieval, deletion, presigned URLs

## Trust Boundaries

See [docs/SECURITY.md](docs/SECURITY.md) for full security documentation.

- **Frontend -> API** — CORS-restricted to configured origins
- **API -> B2** — authenticated via application keys, signature v4
- **Client -> B2** — presigned URLs for playback (inline) and download (attachment); 10-min expiry

## Data Flows

- **Audio Upload**: Browser -> `POST /upload` (multipart) -> API validates -> service orchestrates -> repo writes to B2 at `audio/<YYYY>/<MM>/<safe-filename>--<uuid>.<ext>` -> audio metadata extracted -> response
- **Library list**: Browser -> `GET /library` -> service calls repo with `Prefix="audio/"` -> sorts newest-first -> returns
- **Playback**: Browser -> `GET /library/{key}/playback` -> service validates key -> repo HEADs for existence -> repo generates inline presigned URL -> browser renders `<audio controls>`
- **Download**: Browser -> `GET /library/{key}/download` -> service validates key -> repo generates presigned URL with `Content-Disposition: attachment` -> browser downloads
- **Delete**: Browser -> `DELETE /library/{key}` -> service validates key -> repo deletes from B2 -> TanStack Query invalidates library + stats
- **Bucket explorer**: Browser -> `GET /files` -> service calls repo with empty prefix -> returns full bucket tree

## Observability

- Structured JSON logging on all requests with `request_id`
- Request timing middleware (logs duration per request)
- `/metrics` endpoint (Prometheus format: request count, latency, upload count)
- `/health` endpoint (B2 connectivity check)

## Canonical Files

- Audio Library route handlers: `services/api/app/runtime/library.py`
- Audio Library service orchestration: `services/api/app/service/library.py`
- Audio metadata extractor: `services/api/app/service/audio_metadata.py`
- B2 data access (repo layer): `services/api/app/repo/b2_client.py` (generic file helpers) and `services/api/app/repo/b2_audio.py` (audio-prefix helpers, including `head_audio_objects_parallel`)
- Pydantic models: `services/api/app/types/` (`files.py`, `library.py`, `upload.py`, `stats.py`, `formatting.py`)
- Config (pydantic-settings): `services/api/app/config/settings.py`
- Structural tests: `services/api/tests/test_structure.py`
- Frontend API client: `apps/web/src/lib/api-client.ts`
- Audio Library UI: `apps/web/src/components/library/{library-view,audio-asset-card,waveform}.tsx`
- Shared TypeScript types: `packages/shared/src/types.ts`

## Core Features

- [Audio Library](docs/features/audio-library.md)
- [Audio Upload](docs/features/file-upload.md)
- [Audio Metadata Extraction](docs/features/audio-metadata.md)
- [Audio Playback](docs/features/audio-playback.md)
- [Bucket Explorer](docs/features/file-browser.md)
- [Dashboard](docs/features/dashboard.md)

## References

- [docs/SECURITY.md](docs/SECURITY.md) — security principles and implementation
- [docs/RELIABILITY.md](docs/RELIABILITY.md) — reliability expectations
- [AGENTS.md](AGENTS.md) — architectural invariants and agent instructions
