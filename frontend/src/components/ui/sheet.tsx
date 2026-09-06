import * as React from "react";
import { cn } from "@/lib/utils";

export interface SheetProps {
  open: boolean;
  onClose: () => void;
  children: React.ReactNode;
  className?: string;
}

export function Sheet({ open, onClose, children, className }: SheetProps) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/60 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />
      {/* Drawer Panel */}
      <div
        className={cn(
          "relative z-50 h-full w-full max-w-xl bg-card text-card-foreground shadow-2xl border-l border-border/70 flex flex-col transition-transform animate-in slide-in-from-right duration-200",
          className
        )}
      >
        {children}
      </div>
    </div>
  );
}
