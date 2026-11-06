"use client";

import { AnalysisUnavailable } from "@/components/workspace/analysis-unavailable";

export function InsightsScreen() {
  return <AnalysisUnavailable title="Insights" detail="Account activity analytics are not available yet. Question counts, citation activity and trends are not currently measured." />;
}
