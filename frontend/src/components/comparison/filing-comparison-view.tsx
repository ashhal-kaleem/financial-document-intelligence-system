/**
 * @source shadcn/ui Card + Button + Badge + ScrollArea (registry-fetched)
 * @data Cross-Filing Variance & YoY Comparison Engine
 * @invariant tabular-nums font-mono on metrics and percentages
 * @invariant strictly < 150 lines
 */
"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { GitCompare, ArrowRight, TrendingUp, TrendingDown, Sparkles } from "lucide-react";

interface MetricRow {
  name: string;
  docA: number;
  docB: number;
  unit: string;
}

const COMPARISON_DATA: MetricRow[] = [
  { name: "Total Net Revenue", docA: 383285, docB: 391035, unit: "$M" },
  { name: "Gross Profit", docA: 169148, docB: 180683, unit: "$M" },
  { name: "Operating Expenses (OpEx)", docA: 54847, docB: 56791, unit: "$M" },
  { name: "Operating Income (EBIT)", docA: 114301, docB: 123216, unit: "$M" },
  { name: "Net Income", docA: 96995, docB: 93736, unit: "$M" },
  { name: "Cash & Marketable Securities", docA: 61555, docB: 65162, unit: "$M" },
  { name: "Total Debt", docA: 111088, docB: 105362, unit: "$M" },
];

export function FilingComparisonView() {
  const [docAName] = useState("Apple_10K_FY2023.pdf");
  const [docBName] = useState("Apple_10K_FY2024.pdf");

  return (
    <div className="flex flex-col h-full bg-background overflow-hidden p-4 sm:p-6 space-y-4">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shrink-0">
        <div>
          <h2 className="text-base font-semibold tracking-tight flex items-center gap-2">
            <GitCompare className="size-4 text-primary" /> Multi-Filing YoY Variance Inspector
          </h2>
          <p className="text-xs text-muted-foreground">Compare statement metrics, margins, and footnotes side-by-side</p>
        </div>
        <div className="flex items-center gap-2 text-xs font-mono">
          <Badge variant="outline" className="h-7 px-2.5 bg-card/40">{docAName}</Badge>
          <ArrowRight className="size-3 text-muted-foreground" />
          <Badge variant="default" className="h-7 px-2.5 bg-primary/20 text-primary border-primary/30">{docBName}</Badge>
        </div>
      </div>

      {/* AI Variance Summary Callout */}
      <div className="p-3.5 rounded-lg border border-primary/20 bg-primary/5 flex items-start gap-3 shrink-0">
        <Sparkles className="size-4 text-primary shrink-0 mt-0.5" />
        <div className="text-xs space-y-1">
          <span className="font-semibold text-primary">Key Variance Highlights:</span>
          <p className="text-muted-foreground leading-relaxed">
            Revenue expanded by +2.02% ($7.75B YoY) propelled by Services revenue. Gross margin expanded 200 bps to 46.2%, while total debt decreased by 5.15% ($5.72B deleveraging).
          </p>
        </div>
      </div>

      {/* Comparative Table */}
      <ScrollArea className="flex-1 border border-border/30 rounded-lg bg-card/20">
        <table className="w-full text-xs text-left border-collapse">
          <thead className="border-b border-border/30 bg-card/40 sticky top-0">
            <tr>
              <th className="p-3 font-semibold text-muted-foreground">Financial Benchmark</th>
              <th className="p-3 text-right font-semibold text-muted-foreground font-mono">FY23 Base</th>
              <th className="p-3 text-right font-semibold text-muted-foreground font-mono">FY24 Current</th>
              <th className="p-3 text-right font-semibold text-muted-foreground font-mono">Absolute Delta</th>
              <th className="p-3 text-right font-semibold text-muted-foreground font-mono">Variance (%)</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border/20">
            {COMPARISON_DATA.map((row) => {
              const delta = row.docB - row.docA;
              const pct = ((delta / row.docA) * 100).toFixed(2);
              const isPos = delta >= 0;
              return (
                <tr key={row.name} className="hover:bg-muted/10">
                  <td className="p-3 font-medium">{row.name}</td>
                  <td className="p-3 text-right font-mono tabular-nums text-muted-foreground">
                    ${row.docA.toLocaleString()} {row.unit}
                  </td>
                  <td className="p-3 text-right font-mono tabular-nums font-semibold">
                    ${row.docB.toLocaleString()} {row.unit}
                  </td>
                  <td className="p-3 text-right font-mono tabular-nums">
                    {delta >= 0 ? `+$${delta.toLocaleString()}` : `-$${Math.abs(delta).toLocaleString()}`} {row.unit}
                  </td>
                  <td className="p-3 text-right font-mono tabular-nums">
                    <span className={`inline-flex items-center gap-1 font-semibold ${isPos ? "text-emerald-400" : "text-rose-400"}`}>
                      {isPos ? <TrendingUp className="size-3" /> : <TrendingDown className="size-3" />}
                      {isPos ? "+" : ""}{pct}%
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </ScrollArea>
    </div>
  );
}
