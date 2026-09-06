/**
 * @source shadcn/ui Dialog + Button + Badge (registry-fetched)
 * @client Supabase Native Google OAuth & Session Management
 * @invariant strictly < 150 lines
 * @invariant zero raw button primitives
 */
"use client";

import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useFDISStore } from "@/store/useFDISStore";
import { signInWithGoogle, signOutUser } from "@/lib/supabase";
import { ShieldCheck, Lock, CheckCircle2, LogOut, Sparkles } from "lucide-react";

export function AuthModal() {
  const { isAuthModalOpen, setAuthModalOpen, currentUser, setCurrentUser } = useFDISStore();
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleGoogleSignIn = async () => {
    setLoading(true);
    setErrorMsg(null);
    const { error } = await signInWithGoogle();
    if (error) {
      setErrorMsg(error.message || "Failed to initialize Google sign-in.");
      setLoading(false);
    }
  };

  const handleSignOut = async () => {
    await signOutUser();
    setCurrentUser(null);
    setAuthModalOpen(false);
  };

  return (
    <Dialog open={isAuthModalOpen} onOpenChange={setAuthModalOpen}>
      <DialogContent className="max-w-md w-[92vw] p-6 bg-background/95 backdrop-blur-xl border-border/40 shadow-2xl">
        <DialogHeader>
          <div className="size-10 rounded-xl bg-primary/15 flex items-center justify-center text-primary mb-2">
            <Lock className="size-5" />
          </div>
          <DialogTitle className="text-base font-semibold">
            {currentUser ? "Institutional Account" : "Sign In to FDIS Enterprise"}
          </DialogTitle>
          <p className="text-xs text-muted-foreground">
            {currentUser
              ? "Authenticated session connected to Supabase PostgreSQL Vault"
              : "Access private SEC filings, custom footnote bookmarks, and encrypted audit trails"}
          </p>
        </DialogHeader>

        {currentUser ? (
          <div className="space-y-4 my-2">
            <div className="p-3.5 rounded-lg border border-border/30 bg-card/20 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold">{currentUser.name || "Financial Analyst"}</span>
                <Badge variant="outline" className="text-[10px] font-mono text-emerald-400 border-emerald-500/30">
                  <CheckCircle2 className="size-3 mr-1" /> Active Session
                </Badge>
              </div>
              <p className="text-xs text-muted-foreground font-mono">{currentUser.email}</p>
            </div>

            <Button
              variant="destructive"
              className="w-full gap-2 text-xs active:scale-[0.98]"
              onClick={handleSignOut}
            >
              <LogOut className="size-3.5" /> Sign Out
            </Button>
          </div>
        ) : (
          <div className="space-y-4 my-2">
            {/* Custom Styled Google Sign-In Button */}
            <Button
              variant="outline"
              className="w-full h-11 border-border/40 bg-card/40 hover:bg-muted/10 gap-3 text-xs font-medium active:scale-[0.98] transition-all"
              onClick={handleGoogleSignIn}
              disabled={loading}
            >
              <svg className="size-4" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" />
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" />
              </svg>
              <span>{loading ? "Redirecting to Google..." : "Continue with Google"}</span>
            </Button>

            {errorMsg && (
              <p className="text-xs text-rose-400 font-mono text-center">{errorMsg}</p>
            )}

            {/* Enterprise Security Features */}
            <div className="pt-2 space-y-2 border-t border-border/30">
              <div className="flex items-center gap-2 text-[11px] text-muted-foreground">
                <ShieldCheck className="size-3.5 text-primary" />
                <span>Row Level Security (RLS) encrypted filing storage</span>
              </div>
              <div className="flex items-center gap-2 text-[11px] text-muted-foreground">
                <Sparkles className="size-3.5 text-primary" />
                <span>Puter.js Claude 3.5 Sonnet free inference active</span>
              </div>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
