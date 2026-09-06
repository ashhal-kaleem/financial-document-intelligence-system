/**
 * @source shadcn/ui Dialog + Button + Badge (registry-fetched)
 * @data Unsplash + Pexels + Google Fonts Real-Time Switcher
 * @state Zustand useFDISStore
 * @invariant strictly < 150 lines
 * @invariant zero raw button primitives
 */
"use client";

import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { useFDISStore, BackgroundTheme, TypographyFont } from "@/store/useFDISStore";
import { Palette, Check } from "lucide-react";

interface ThemeCustomizerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const WALLPAPERS: { id: BackgroundTheme; name: string; source: string; preview: string }[] = [
  { id: "emerald", name: "Emerald Fluid Ambient", source: "Unsplash API", preview: "bg-emerald-950/40" },
  { id: "wallstreet", name: "Wall Street Floor", source: "Pexels API", preview: "bg-blue-950/40" },
  { id: "slate", name: "Obsidian Terminal", source: "Minimalist Dark", preview: "bg-zinc-950" },
];

const FONTS: { id: TypographyFont; name: string; sample: string }[] = [
  { id: "inter", name: "Inter", sample: "Enterprise Standard" },
  { id: "outfit", name: "Outfit", sample: "Modern Geometrical" },
  { id: "roboto", name: "Roboto", sample: "Google WebFont Classic" },
  { id: "mono", name: "JetBrains Mono", sample: "Technical Terminal" },
];

export function ThemeCustomizer({ open, onOpenChange }: ThemeCustomizerProps) {
  const { activeBackground, setActiveBackground, activeFont, setActiveFont } = useFDISStore();

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md w-[92vw] p-5 bg-background/95 backdrop-blur-xl border-border/40 shadow-2xl">
        <DialogHeader>
          <DialogTitle className="text-base font-semibold flex items-center gap-2">
            <Palette className="size-4 text-primary" /> Visual & Typography Studio
          </DialogTitle>
          <p className="text-xs text-muted-foreground">
            Powered by Unsplash, Pexels, and Google Fonts APIs
          </p>
        </DialogHeader>

        {/* Wallpaper Picker */}
        <div className="space-y-2.5 mt-2">
          <span className="text-xs font-medium text-muted-foreground block">Ambient Wallpaper Background</span>
          <div className="grid grid-cols-1 gap-2">
            {WALLPAPERS.map((wp) => {
              const isSelected = activeBackground === wp.id;
              return (
                <Button
                  variant="outline"
                  key={wp.id}
                  onClick={() => setActiveBackground(wp.id)}
                  className={`h-auto flex items-center justify-between p-3 rounded-lg border text-left transition-all active:scale-[0.98] ${
                    isSelected ? "border-primary bg-primary/10 shadow-sm" : "border-border/30 bg-card/20 hover:bg-muted/10"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className={`size-7 rounded border border-border/30 ${wp.preview}`} />
                    <div>
                      <span className="text-xs font-semibold block">{wp.name}</span>
                      <span className="text-[10px] text-muted-foreground font-normal">{wp.source}</span>
                    </div>
                  </div>
                  {isSelected && <Check className="size-4 text-primary" />}
                </Button>
              );
            })}
          </div>
        </div>

        {/* Font Picker */}
        <div className="space-y-2.5 mt-3">
          <span className="text-xs font-medium text-muted-foreground block">Google Fonts Typography</span>
          <div className="grid grid-cols-2 gap-2">
            {FONTS.map((f) => {
              const isSelected = activeFont === f.id;
              return (
                <Button
                  variant="outline"
                  key={f.id}
                  onClick={() => setActiveFont(f.id)}
                  className={`h-auto p-2.5 flex flex-col items-stretch text-left transition-all active:scale-[0.98] ${
                    isSelected ? "border-primary bg-primary/10" : "border-border/30 bg-card/20 hover:bg-muted/10"
                  }`}
                >
                  <div className="flex items-center justify-between w-full">
                    <span className="text-xs font-medium">{f.name}</span>
                    {isSelected && <Check className="size-3 text-primary" />}
                  </div>
                  <span className="text-[10px] text-muted-foreground block mt-0.5 truncate font-normal">{f.sample}</span>
                </Button>
              );
            })}
          </div>
        </div>

        <div className="mt-4 pt-3 border-t border-border/30 flex justify-end">
          <Button size="sm" onClick={() => onOpenChange(false)} className="text-xs active:scale-[0.98]">
            Apply Changes
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
