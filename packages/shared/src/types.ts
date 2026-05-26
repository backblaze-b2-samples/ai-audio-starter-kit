export type FileStatus = "uploading" | "complete" | "error";

export interface FileMetadata {
  key: string;
  filename: string;
  folder: string;
  size_bytes: number;
  size_human: string;
  content_type: string;
  uploaded_at: string;
  url: string | null;
}

export interface FileMetadataDetail {
  filename: string;
  size_bytes: number;
  size_human: string;
  mime_type: string;
  extension: string;
  md5: string;
  sha256: string;
  uploaded_at: string;
  // Audio-specific (populated when content_type starts with audio/)
  duration_ms: number | null;
  sample_rate: number | null;
  channels: number | null;
  bit_depth: number | null;
  codec: string | null;
}

export interface FileUploadResponse {
  key: string;
  filename: string;
  size_bytes: number;
  size_human: string;
  content_type: string;
  uploaded_at: string;
  url: string | null;
  metadata: FileMetadataDetail | null;
}

export interface DailyUploadCount {
  date: string;
  uploads: number;
  duration_ms: number;
}

export interface UploadStats {
  total_files: number;
  total_size_bytes: number;
  total_size_human: string;
  uploads_today: number;
  total_downloads: number;
  total_audio_assets: number;
  total_duration_ms: number;
  audio_size_bytes: number;
  audio_size_human: string;
  formats: Record<string, number>;
}

/** An audio asset stored under the `audio/` prefix in B2. */
export interface AudioAsset {
  key: string;
  size_bytes: number;
  size_human: string;
  content_type: string;
  created_at: string;
  duration_ms: number | null;
  sample_rate: number | null;
  channels: number | null;
  bit_depth: number | null;
  codec: string | null;
  title_preview: string | null;
}
