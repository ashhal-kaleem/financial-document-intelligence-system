"use client";

import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import { useFDISStore } from "@/store/useFDISStore";
import { endSession } from "@/lib/api";
import { ensureGuestSession, getSupabase } from "@/lib/supabase";

/**
 * Guest session control: no accounts, no login. Shows what the private guest
 * session means and offers explicit "End session & delete my data".
 */
export function SessionMenu() {
  const { isSessionMenuOpen, setSessionMenuOpen, setCurrentUser } =
    useFDISStore();
  const queryClient = useQueryClient();
  const [confirming, setConfirming] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [done, setDone] = useState("");

  if (!isSessionMenuOpen) return null;

  const close = () => {
    setSessionMenuOpen(false);
    setConfirming(false);
    setBusy(false);
    setError("");
    setDone("");
  };

  const endNow = async () => {
    setBusy(true);
    setError("");
    try {
      const result = await endSession();
      await getSupabase()?.auth.signOut();
      queryClient.removeQueries({ queryKey: ["documents"] });
      setCurrentUser(null);
      const { error: sessionError } = await ensureGuestSession();
      if (sessionError) {
        setError(
          "Your data was deleted, but a fresh guest session could not start. Reload the page.",
        );
        return;
      }
      setDone(
        result.documents_failed
          ? `Session ended. ${result.documents_deleted} PDF(s) deleted; ${result.documents_failed} could not be confirmed deleted. A fresh private session started.`
          : "Session ended and your data was deleted. A fresh private session started.",
      );
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Session cleanup failed. Retry before leaving this device.",
      );
    } finally {
      setBusy(false);
      setConfirming(false);
    }
  };

  return (
    <Dialog open={isSessionMenuOpen} onOpenChange={close}>
      <DialogContent
        aria-labelledby="session-title"
        className="v8-min w-[92vw] max-w-sm rounded-[28px] bg-white p-8 shadow-2xl"
      >
        <h2 id="session-title" className="text-[18px] font-semibold fam-ink">
          Private guest session
        </h2>
        <p className="mt-2 text-[12px] leading-relaxed fam-sub">
          No account or login. Your PDFs and questions are visible only in
          this tab. Closing the tab ends your access: a new tab starts empty.
          Any PDFs left behind are deleted automatically within about a day.
        </p>
        {done ? (
          <p role="status" className="mt-4 text-[13px] text-[#174A37]">
            {done}
          </p>
        ) : confirming ? (
          <>
            <p className="mt-4 text-[13px] font-medium text-[#7A2E2E]">
              Delete all your PDFs and end this session now? This cannot be
              undone.
            </p>
            <div className="mt-4 flex gap-2">
              <button
                disabled={busy}
                onClick={endNow}
                className="flex-1 rounded-full bg-[#7A2E2E] py-3 text-[13px] font-medium text-white disabled:opacity-50"
              >
                {busy ? "Deleting..." : "Yes, delete my data"}
              </button>
              <button
                disabled={busy}
                onClick={() => setConfirming(false)}
                className="flex-1 rounded-full border py-3 text-[13px]"
              >
                Keep session
              </button>
            </div>
          </>
        ) : (
          <button
            onClick={() => setConfirming(true)}
            className="mt-6 w-full rounded-full bg-[#1C1F2E] py-3 text-[13px] font-medium text-white"
          >
            End session &amp; delete my data
          </button>
        )}
        {error && (
          <p role="alert" className="mt-3 text-sm text-red-800">
            {error}
          </p>
        )}
      </DialogContent>
    </Dialog>
  );
}
