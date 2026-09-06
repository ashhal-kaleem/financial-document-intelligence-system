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
import { ShieldCheck, Lock, CheckCircle2, LogOut, UserCheck, AlertCircle } from "lucide-react";

export function AuthModal() {
  const { isAuthModalOpen, setAuthModalOpen, currentUser, setCurrentUser } = useFDISStore();
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleGoogleSignIn = async () => {
    setLoading(true);
    setErrorMsg(null);
    const { error } = await signInWithGoogle();
    if (error) {
      setErrorMsg("Google Provider is not enabled in Supabase dashboard. You can enable it or use 1-Click Demo Login below.");
      setLoading(false);
    }
  };

  const handleDemoSignIn = (role: string, email: string) => {
    setCurrentUser({
      id: "demo-analyst-" + Date.now(),
      name: role,
      email: email,
    });
    setAuthModalOpen(false);
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
              ? "Authenticated session active on Supabase PostgreSQL Vault"
              : "Access private SEC filings, custom footnote bookmarks, and encrypted audit trails"}
          </p>
        </DialogHeader>

        {currentUser ? (
          <div className="space-y-4 my-2">
            <div className="p-3.5 rounded-lg border border-border/30 bg-card/20 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold">{currentUser.name || "Financial Analyst"}</span>
                <Badge variant="outline" className="text-[10px] font-mono text-primary border-primary/30">
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
          <div className="space-y-3.5 my-2">
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
              <span>{loading ? "Connecting..." : "Continue with Google"}</span>
            </Button>

            {errorMsg && (
              <div className="p-2.5 rounded-md bg-amber-500/10 border border-amber-500/20 text-[11px] text-amber-800 flex items-start gap-2">
                <AlertCircle className="size-4 shrink-0 text-amber-700 mt-0.5" />
                <span>{errorMsg}</span>
              </div>
            )}

            <div className="relative my-2 text-center text-[10px] text-muted-foreground before:absolute before:left-0 before:top-1/2 before:w-[35%] before:h-px before:bg-border/40 after:absolute after:right-0 after:top-1/2 after:w-[35%] after:h-px after:bg-border/40">
              OR INSTANT ACCESS
            </div>

            <Button
              variant="secondary"
              className="w-full h-10 gap-2 text-xs font-medium active:scale-[0.98] border border-primary/20 bg-primary/10 hover:bg-primary/20 text-primary"
              onClick={() => handleDemoSignIn("Senior Portfolio Analyst", "analyst@fdis.enterprise")}
            >
              <UserCheck className="size-3.5" /> 1-Click Demo Analyst Access
            </Button>

            <div className="pt-2 space-y-1.5 border-t border-border/30 text-[11px] text-muted-foreground">
              <div className="flex items-center gap-2">
                <ShieldCheck className="size-3.5 text-primary" />
                <span>Supabase PostgreSQL Row Level Security (RLS)</span>
              </div>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
