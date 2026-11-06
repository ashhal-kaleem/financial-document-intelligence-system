"use client";

import { AnalysisUnavailable } from "@/components/workspace/analysis-unavailable";

export function StatementsScreen() {
  return (
    <AnalysisUnavailable
      title="Statements"
      detail="Structured statement extraction is not available yet. Use document Q&A to request source-cited figures from a ready PDF."
    />
  );
}
