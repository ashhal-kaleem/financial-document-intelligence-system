/**
 * @source shadcn/ui Button + Avatar + DropdownMenu + Badge (registry-fetched)
 * @auth Supabase Google OAuth Custom Dialog
 * @icons Lucide React
 * @state Zustand useFDISStore
 * @invariant strictly < 150 lines
 * @invariant zero raw button primitives
 */
"use client";

import { useEffect, useState } from "react";
import { FileText, Palette, FileDown, DollarSign, GitCompare, MessageSquare, LogIn } from "lucide-react";
import { Button } from "@/components/ui/button";
import { UserAvatar } from "@/components/ui/user-avatar";
import { useFDISStore, DashboardTab } from "@/store/useFDISStore";
import { ThemeCustomizer } from "@/components/settings/theme-customizer";
import { getSessionUser } from "@/lib/supabase";

export function DashboardHeader() {
  const { activeTab, setActiveTab, setExportModalOpen, setAuthModalOpen, currentUser, setCurrentUser } = useFDISStore();
  const [themeOpen, setThemeOpen] = useState(false);

  useEffect(() => {
    getSessionUser().then((user) => {
      if (user) {
        setCurrentUser({
          id: user.id,
          email: user.email,
          name: user.user_metadata?.full_name || user.email?.split("@")[0] || "Financial Analyst",
          avatarUrl: user.user_metadata?.avatar_url,
        });
      }
    });
  }, [setCurrentUser]);

  const TABS: { id: DashboardTab; label: string; icon: typeof MessageSquare }[] = [
    { id: "chat", label: "Intelligence Q&A", icon: MessageSquare },
    { id: "statements", label: "Financial Statements", icon: DollarSign },
    { id: "comparison", label: "YoY Comparison", icon: GitCompare },
  ];

  return (
    <header className="flex h-14 shrink-0 items-center justify-between border-b border-border/40 bg-card/60 px-4 backdrop-blur-sm z-20">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2.5">
          <div className="flex size-8 items-center justify-center rounded-lg bg-primary/15 text-primary">
            <FileText className="size-4" strokeWidth={1.75} />
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-semibold tracking-tight">FDIS</span>
            <span className="text-[10px] leading-none text-muted-foreground">Financial Intelligence</span>
          </div>
        </div>

        <div className="hidden md:flex items-center gap-1 bg-muted/40 p-1 rounded-lg border border-border/30">
          {TABS.map((t) => {
            const Icon = t.icon;
            const isSelected = activeTab === t.id;
            return (
              <Button
                key={t.id}
                variant={isSelected ? "secondary" : "ghost"}
                size="sm"
                onClick={() => setActiveTab(t.id)}
                className={`h-7 px-3 text-xs gap-1.5 active:scale-[0.98] ${
                  isSelected ? "bg-background text-foreground shadow-sm font-medium" : "text-muted-foreground"
                }`}
              >
                <Icon className="size-3.5" />
                {t.label}
              </Button>
            );
          })}
        </div>
      </div>

      <div className="flex items-center gap-1.5 sm:gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => setExportModalOpen(true)}
          className="h-8 gap-1.5 text-xs active:scale-[0.98] hidden sm:inline-flex"
        >
          <FileDown className="size-3.5 text-primary" /> Export Memo
        </Button>

        <Button
          variant="ghost"
          size="icon"
          onClick={() => setThemeOpen(true)}
          className="size-8 active:scale-[0.98]"
          title="Customize Theme & Fonts"
        >
          <Palette className="size-4 text-muted-foreground hover:text-foreground" />
        </Button>

        <div className="h-5 w-px bg-border/40 mx-1 hidden sm:block" />

        {currentUser ? (
          <Button
            variant="ghost"
            className="h-8 px-2 gap-2 text-xs active:scale-[0.98]"
            onClick={() => setAuthModalOpen(true)}
          >
            <UserAvatar name={currentUser.name || "Analyst"} email={currentUser.email || ""} size="sm" />
            <span className="max-w-[100px] truncate hidden sm:inline-block">{currentUser.name}</span>
          </Button>
        ) : (
          <Button
            variant="outline"
            size="sm"
            onClick={() => setAuthModalOpen(true)}
            className="h-8 gap-1.5 text-xs font-medium border-primary/30 text-primary hover:bg-primary/10 active:scale-[0.98]"
          >
            <LogIn className="size-3.5" /> Sign In
          </Button>
        )}
      </div>

      <ThemeCustomizer open={themeOpen} onOpenChange={setThemeOpen} />
    </header>
  );
}
