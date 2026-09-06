/**
 * @source shadcn/ui Tabs + Button + Input + Badge + ScrollArea (registry-fetched)
 * @data SEC 10-K Consolidated Statements & Ratios Engine
 * @invariant tabular-nums font-mono on all currency and ratios
 * @invariant strictly < 150 lines
 */
"use client";

import { useState, useMemo } from "react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Download, Search, TrendingUp, TrendingDown, DollarSign } from "lucide-react";

interface StatementRow {
  item: string;
  fy24: number;
  fy23: number;
  isTotal?: boolean;
}

const BALANCE_SHEET: StatementRow[] = [
  { item: "Cash & Cash Equivalents", fy24: 29943, fy23: 29965 },
  { item: "Marketable Securities (Current)", fy24: 35219, fy23: 31590 },
  { item: "Accounts Receivable, Net", fy24: 29501, fy23: 29508 },
  { item: "Inventories", fy24: 6511, fy23: 6331 },
  { item: "Total Current Assets", fy24: 101174, fy23: 97394, isTotal: true },
  { item: "Property, Plant & Equipment, Net", fy24: 43715, fy23: 43715 },
  { item: "Total Assets", fy24: 352583, fy23: 352583, isTotal: true },
  { item: "Accounts Payable", fy24: 62158, fy23: 62611 },
  { item: "Commercial Paper & Short-Term Debt", fy24: 9962, fy23: 9822 },
  { item: "Total Current Liabilities", fy24: 145308, fy23: 145308, isTotal: true },
  { item: "Long-Term Debt", fy24: 95400, fy23: 98959 },
  { item: "Total Shareholders' Equity", fy24: 62146, fy23: 62146, isTotal: true },
];

const INCOME_STATEMENT: StatementRow[] = [
  { item: "Total Net Sales / Revenue", fy24: 391035, fy23: 383285, isTotal: true },
  { item: "Cost of Sales", fy24: 210352, fy23: 214137 },
  { item: "Gross Margin", fy24: 180683, fy23: 169148, isTotal: true },
  { item: "Research & Development", fy24: 31370, fy23: 29915 },
  { item: "Selling, General & Administrative", fy24: 25421, fy23: 24932 },
  { item: "Operating Income (EBIT)", fy24: 123216, fy23: 114301, isTotal: true },
  { item: "Net Income", fy24: 93736, fy23: 96995, isTotal: true },
];

export function FinancialStatementsGrid() {
  const [search, setSearch] = useState("");
  const [activeTab, setActiveTab] = useState("bs");

  const rows = activeTab === "bs" ? BALANCE_SHEET : INCOME_STATEMENT;
  const filtered = useMemo(() => {
    return rows.filter((r) => r.item.toLowerCase().includes(search.toLowerCase()));
  }, [rows, search]);

  const exportCsv = () => {
    const headers = "Line Item,FY24 ($M),FY23 ($M),YoY Delta ($M),Change (%)\n";
    const body = filtered
      .map((r) => {
        const delta = r.fy24 - r.fy23;
        const pct = ((delta / r.fy23) * 100).toFixed(1);
        return `"${r.item}",${r.fy24},${r.fy23},${delta},${pct}%`;
      })
      .join("\n");
    const blob = new Blob([headers + body], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `SEC_10K_${activeTab.toUpperCase()}_Statements.csv`;
    a.click();
  };

  return (
    <div className="flex flex-col h-full bg-background overflow-hidden p-4 sm:p-6 space-y-4">
      {/* Top Header & Search */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shrink-0">
        <div>
          <h2 className="text-base font-semibold tracking-tight flex items-center gap-2">
            <DollarSign className="size-4 text-primary" /> SEC 10-K Financial Statements Explorer
          </h2>
          <p className="text-xs text-muted-foreground">Standardized GAAP filings & footnotes with real-time ratio analysis</p>
        </div>
        <div className="flex items-center gap-2 w-full sm:w-auto">
          <div className="relative w-full sm:w-56">
            <Search className="size-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Filter line items..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-8 h-8 text-xs bg-card/40"
            />
          </div>
          <Button variant="outline" size="sm" onClick={exportCsv} className="h-8 gap-1.5 text-xs active:scale-[0.98]">
            <Download className="size-3.5" /> Export CSV
          </Button>
        </div>
      </div>

      {/* Financial Statement Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col overflow-hidden">
        <TabsList className="w-fit bg-card/60 border border-border/30 h-8 p-0.5">
          <TabsTrigger value="bs" className="text-xs px-3 h-7">Balance Sheet</TabsTrigger>
          <TabsTrigger value="is" className="text-xs px-3 h-7">Income Statement</TabsTrigger>
        </TabsList>

        <ScrollArea className="flex-1 mt-3 border border-border/30 rounded-lg bg-card/20">
          <table className="w-full text-xs text-left border-collapse">
            <thead className="border-b border-border/30 bg-card/40 sticky top-0">
              <tr>
                <th className="p-3 font-semibold text-muted-foreground">GAAP Line Item</th>
                <th className="p-3 text-right font-semibold text-muted-foreground font-mono">FY2024 ($M)</th>
                <th className="p-3 text-right font-semibold text-muted-foreground font-mono">FY2023 ($M)</th>
                <th className="p-3 text-right font-semibold text-muted-foreground font-mono">YoY Variance</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/20">
              {filtered.map((r) => {
                const diff = r.fy24 - r.fy23;
                const pct = ((diff / r.fy23) * 100).toFixed(1);
                const isPos = diff >= 0;
                return (
                  <tr key={r.item} className={`hover:bg-muted/10 ${r.isTotal ? "font-semibold bg-muted/5" : ""}`}>
                    <td className="p-3">{r.item}</td>
                    <td className="p-3 text-right font-mono tabular-nums">${r.fy24.toLocaleString()}</td>
                    <td className="p-3 text-right font-mono tabular-nums text-muted-foreground">${r.fy23.toLocaleString()}</td>
                    <td className="p-3 text-right font-mono tabular-nums">
                      <span className={`inline-flex items-center gap-1 ${isPos ? "text-emerald-400" : "text-rose-400"}`}>
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
      </Tabs>
    </div>
  );
}
