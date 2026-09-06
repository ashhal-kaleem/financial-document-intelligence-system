/**
 * @source shadcn/ui Card + Badge + Skeleton (registry-fetched)
 * @data Mockaroo API seed fixtures
 * @icons Lucide React
 * @invariant tabular-nums on all financial numbers
 */
"use client";

import { FileText, Brain, Layers, Zap } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useQuery } from "@tanstack/react-query";
import { fetchDocuments } from "@/lib/api";
import { useHydrated } from "@/hooks/useHydrated";

interface KPIMetric {
  label: string;
  value: string;
  change: string;
  trend: "up" | "down" | "neutral";
  icon: React.ReactNode;
}

function KPICard({ metric }: { metric: KPIMetric }) {
  return (
    <Card className="border-border/30 bg-card/60 backdrop-blur-sm transition-all duration-200 hover:border-border/50 hover:bg-card/80">
      <CardContent className="flex items-center gap-4 p-4">
        <div className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-primary/10">
          {metric.icon}
        </div>
        <div className="flex flex-col gap-0.5">
          <span className="text-xs text-muted-foreground">{metric.label}</span>
          <span className="text-lg font-semibold tabular-nums font-mono tracking-tight">
            {metric.value}
          </span>
        </div>
        <Badge
          variant={metric.trend === "up" ? "default" : "secondary"}
          className="ml-auto text-[10px] tabular-nums"
        >
          {metric.change}
        </Badge>
      </CardContent>
    </Card>
  );
}

function KPICardSkeleton() {
  return (
    <Card className="border-border/30 bg-card/60">
      <CardContent className="flex items-center gap-4 p-4">
        <Skeleton className="size-10 rounded-lg" />
        <div className="flex flex-col gap-1.5">
          <Skeleton className="h-3 w-20" />
          <Skeleton className="h-5 w-14" />
        </div>
        <Skeleton className="ml-auto h-5 w-12 rounded-full" />
      </CardContent>
    </Card>
  );
}

export function KPIStrip() {
  const isHydrated = useHydrated();
  const { data: docs, isLoading } = useQuery({
    queryKey: ["documents"],
    queryFn: fetchDocuments,
    enabled: isHydrated,
  });

  if (!isHydrated || isLoading) {
    return (
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <KPICardSkeleton key={i} />
        ))}
      </div>
    );
  }

  const processed = docs?.filter((d) => d.status === "ready").length ?? 0;
  const total = docs?.length ?? 0;
  const totalChunks = docs?.reduce((acc, d) => acc + (d.chunk_count || 0), 0) ?? 0;

  const metrics: KPIMetric[] = [
    {
      label: "Uploaded Filings",
      value: total.toString(),
      change: total > 0 ? "Active" : "Empty",
      trend: "up",
      icon: <FileText className="size-5 text-primary" strokeWidth={1.75} />,
    },
    {
      label: "Processed & Ready",
      value: processed.toString(),
      change: `${total > 0 ? Math.round((processed / total) * 100) : 0}% ready`,
      trend: "up",
      icon: <Brain className="size-5 text-primary" strokeWidth={1.75} />,
    },
    {
      label: "Vector Chunks",
      value: totalChunks.toString(),
      change: totalChunks > 0 ? "pgvector" : "0 chunks",
      trend: "up",
      icon: <Layers className="size-5 text-primary" strokeWidth={1.75} />,
    },
    {
      label: "Engine Latency",
      value: "Sub-second",
      change: "Accelerated",
      trend: "up",
      icon: <Zap className="size-5 text-primary" strokeWidth={1.75} />,
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
      {metrics.map((metric) => (
        <KPICard key={metric.label} metric={metric} />
      ))}
    </div>
  );
}
