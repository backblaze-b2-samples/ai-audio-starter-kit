"use client";

import Link from "next/link";
import { AudioLines, Upload } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { FormatBreakdown } from "@/components/dashboard/format-breakdown";
import { RecentUploadsTable } from "@/components/dashboard/recent-uploads-table";
import { StatsCards } from "@/components/dashboard/stats-cards";
import { UploadChart } from "@/components/dashboard/upload-chart";
import { useFileStats } from "@/lib/queries";

/**
 * Dashboard body. Splits into two layouts driven by `useFileStats()`:
 *
 *  - **Empty bucket** (`total_audio_assets === 0`, not loading/erroring):
 *    a single hero card prompting the first upload. We deliberately keep
 *    `StatsCards`/charts/table off-screen here — they're all-zero on an
 *    empty bucket and dilute the call to action.
 *  - **Populated**: the usual StatsCards + FormatBreakdown + chart/table grid.
 *
 * Errors and the initial loading state both fall through to the populated
 * layout so the child components can render their own skeletons / error UI
 * (consistent with the rest of the app).
 */
export function DashboardView() {
  const { data: stats, isLoading, error } = useFileStats();
  const isEmpty =
    !isLoading && !error && stats?.total_audio_assets === 0;

  if (isEmpty) {
    return (
      <Card className="animate-fade-in-up">
        <CardContent className="p-0">
          <EmptyState
            icon={AudioLines}
            title="No audio yet — upload your first track"
            description="Drop a wav, mp3, flac, or ogg file to see it appear in your dashboard, library, and recent uploads."
            action={
              <Button asChild size="sm" className="h-8">
                <Link href="/upload">
                  <Upload className="h-3.5 w-3.5" />
                  Upload audio
                </Link>
              </Button>
            }
          />
        </CardContent>
      </Card>
    );
  }

  return (
    <>
      <StatsCards />
      <FormatBreakdown />
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="animate-fade-in-up stagger-3">
          <UploadChart />
        </div>
        <div className="animate-fade-in-up stagger-4">
          <RecentUploadsTable />
        </div>
      </div>
    </>
  );
}
