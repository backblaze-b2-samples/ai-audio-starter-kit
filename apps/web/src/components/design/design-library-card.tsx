"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AudioAssetCard } from "@/components/library/audio-asset-card";
import { Section } from "./section";
import type { AudioAsset } from "@ai-audio-starter-kit/shared";

// Static demo asset — keys, sizes, timestamps are fabricated. Play /
// Download will toast a failure when clicked since the key doesn't
// resolve in B2; that's the intended showcase behavior.
const sampleAsset: AudioAsset = {
  key: "audio/2026/05/00000000-0000-4000-8000-000000000001.wav",
  size_bytes: 287_440,
  size_human: "280.7 KB",
  content_type: "audio/wav",
  created_at: "2026-05-20T14:23:00.000Z",
  duration_ms: 12_400,
  sample_rate: 44_100,
  channels: 2,
  bit_depth: 16,
  codec: "wav",
  title_preview: "demo-asset.wav",
};

export function DesignLibraryCard() {
  return (
    <Section
      id="audio-library-card"
      title="Audio Library Card"
      description="The default library primitive for audio samples on this kit. Renders an audio asset with a metadata strip, an inline waveform stub, and Play / Download / Delete actions. Compose into any grid scoped to the audio/ prefix."
    >
      <Card>
        <CardHeader className="border-b border-border py-4 px-5">
          <CardTitle className="card-title">Sample asset</CardTitle>
        </CardHeader>
        <CardContent className="p-5">
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            <AudioAssetCard asset={sampleAsset} />
          </div>
          <p className="text-xs text-muted-foreground mt-4">
            Source: <code className="font-mono">apps/web/src/components/library/audio-asset-card.tsx</code> ·
            also documented in <code className="font-mono">docs/features/audio-library.md</code>.
          </p>
        </CardContent>
      </Card>
    </Section>
  );
}
