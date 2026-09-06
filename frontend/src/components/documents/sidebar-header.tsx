/**
 * @source shadcn/ui Button + Input (registry-fetched)
 * @icons Lucide React
 * @invariant strictly < 150 lines
 * @invariant zero raw button primitives
 */
"use client";

import { Search, Filter } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface SidebarHeaderProps {
  searchQuery: string;
  onSearchChange: (query: string) => void;
}

export function SidebarHeader({
  searchQuery,
  onSearchChange,
}: SidebarHeaderProps) {
  return (
    <div className="flex flex-col gap-3 border-b border-border/40 p-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold tracking-tight">
          Filing Index
        </h2>
        <div className="flex gap-1">
          <Button
            variant="ghost"
            size="icon"
            className="size-7 text-muted-foreground hover:text-foreground"
            aria-label="Filter filings"
          >
            <Filter className="size-3.5" strokeWidth={1.75} />
          </Button>
        </div>
      </div>
      <div className="relative">
        <Search className="absolute left-2.5 top-1/2 size-3.5 -translate-y-1/2 text-muted-foreground" />
        <Input
          type="text"
          placeholder="Search filings..."
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          className="h-8 pl-8 text-xs"
        />
      </div>
    </div>
  );
}
