"use client";
import { useState, useEffect, useRef } from "react";
import { loadPuter, PUTER_MODELS } from "@/lib/puter-ai";
import { useFDISStore } from "@/store/useFDISStore";

export function AIConnection({
  connected,
  setConnected,
  model,
  setModel,
}: {
  connected: boolean;
  setConnected: (v: boolean) => void;
  model: string;
  setModel: (v: string) => void;
}) {
  const owner = useFDISStore((s) => s.currentUser?.id);
  const dialogRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const [open, setOpen] = useState(false);
  const [sdkReady, setSDKReady] = useState(false);
  const [consent, setConsent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    setConsent(false);
    setConnected(false);
    setError("");
  }, [owner, setConnected]);
  useEffect(() => {
    if (!open) return;
    const box = dialogRef.current;
    const focusables = () =>
      Array.from(
        box?.querySelectorAll<HTMLElement>(
          "button:not(:disabled), select, input, summary, a[href]",
        ) || [],
      );
    focusables()[0]?.focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setOpen(false);
        return;
      }
      if (e.key !== "Tab") return;
      const els = focusables();
      const first = els[0];
      const last = els[els.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last?.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first?.focus();
      }
    };
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("keydown", onKey);
      triggerRef.current?.focus();
    };
  }, [open]);
  const connect = async () => {
    if (!owner) {
      setOpen(false);
      useFDISStore.getState().setAuthModalOpen(true);
      return;
    }
    if (!consent) return;
    setBusy(true);
    setError("");
    try {
      const sdk = await loadPuter();
      setSDKReady(true);
      // Popup must be initiated by a click. A second explicit click after script loading preserves it.
      if (!sdk.auth.isSignedIn()) {
        setError(
          "AI connection loaded. Click Authorize Puter to open its popup.",
        );
        return;
      }
      if (useFDISStore.getState().currentUser?.id === owner) setConnected(true);
    } catch {
      if (useFDISStore.getState().currentUser?.id === owner)
        setError("AI connection could not load. Retry.");
    } finally {
      setBusy(false);
    }
  };
  const authorize = async () => {
    if (!window.puter || !owner || !consent) return;
    setBusy(true);
    setError("");
    try {
      await window.puter.auth.signIn();
      if (useFDISStore.getState().currentUser?.id === owner) setConnected(true);
    } catch {
      if (useFDISStore.getState().currentUser?.id === owner)
        setError(
          "Puter connection was cancelled or failed. No question was sent.",
        );
    } finally {
      setBusy(false);
    }
  };
  return (
    <section className="shrink-0 border-b border-[#ECE8F6] bg-white px-6 py-2 text-xs">
      <div className="flex min-h-10 items-center justify-between gap-3">
        <span className="text-[#6E6A78]">
          {connected
            ? "Puter AI connected"
            : "Connect your AI to ask about reports"}
        </span>
        <button
          ref={triggerRef}
          onClick={() => setOpen(true)}
          className="shrink-0 rounded-full bg-[#EEE9FA] px-4 py-2.5 font-medium text-[#8063DB] hover:bg-[#E4DCF8]"
        >
          {connected ? "AI settings" : "Connect AI"}
        </button>
      </div>
      {open && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/25 p-4"
          onClick={() => setOpen(false)}
        >
          <div
            ref={dialogRef}
            role="dialog"
            aria-modal="true"
            aria-labelledby="ai-settings-title"
            className="max-h-[90dvh] w-full max-w-lg overflow-y-auto rounded-3xl bg-[#FDFDFD] p-6 shadow-xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="mb-4 flex items-center justify-between gap-3">
              <h2
                id="ai-settings-title"
                className="text-lg font-semibold text-[#141414]"
              >
                Workspace AI
              </h2>
              <button
                aria-label="Close AI settings"
                onClick={() => setOpen(false)}
                className="size-10 rounded-full bg-[#F1EDF8] text-lg text-[#8063DB]"
              >
                ×
              </button>
            </div>
            <p className="mb-4 leading-5 text-[#6E6A78]">
              Sign in to FDIS with Google to access your reports. Puter connects
              separately for AI answers.
            </p>
            <label className="block font-medium">
              Free model variant
              <select
                value={model}
                onChange={(e) => setModel(e.target.value)}
                className="mt-2 min-h-11 w-full rounded-xl border border-[#E5DFF2] bg-white px-3 text-[#443957] outline-none focus:ring-2 focus:ring-[#CDBDF3]"
                aria-label="AI model"
              >
                <option value="">Choose a free model</option>
                {PUTER_MODELS.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.name}
                  </option>
                ))}
              </select>
            </label>
            {connected && (
              <button
                className="mt-4 min-h-11 rounded-full border border-[#E5DFF2] px-4 text-[#8063DB]"
                onClick={() => {
                  window.puter?.auth.signOut();
                  setConnected(false);
                  setConsent(false);
                }}
              >
                Disconnect AI
              </button>
            )}
            {!connected && (
              <>
                <details className="mt-2">
                  <summary className="min-h-10 cursor-pointer py-2 underline">
                    What is shared, costs and privacy
                  </summary>
                  <div className="pr-1">
                    <p className="leading-5">
                      Questions, retrieved report excerpts, filenames and page
                      metadata go to Puter and the selected model provider when
                      you ask. The original PDF and FDIS token are not sent.
                      Review confidential report permissions first.
                    </p>
                    <p className="mt-1 leading-5 text-[#6E6A78]">
                      Connecting loads Puter's third-party SDK. AI use is
                      metered to your Puter account; limits or other account
                      charges may still apply. Cancelling stops waiting, but a
                      model request already sent may finish and be billed.
                      Answers appear after completion and citation-ID checks,
                      not token by token. Citations are checked for valid IDs,
                      not semantic truth.{" "}
                      <a
                        className="underline"
                        href="https://puter.com/privacy"
                        target="_blank"
                        rel="noreferrer"
                      >
                        Puter privacy
                      </a>{" "}
                      ·{" "}
                      <a
                        className="underline"
                        href="https://docs.puter.com/rate-limits-and-quotas/"
                        target="_blank"
                        rel="noreferrer"
                      >
                        Limits
                      </a>
                    </p>
                  </div>
                </details>
                <label className="flex min-h-10 items-start gap-2 py-2 leading-5">
                  <input
                    className="mt-1 size-4 shrink-0"
                    type="checkbox"
                    checked={consent}
                    onChange={(e) => setConsent(e.target.checked)}
                  />
                  <span>
                    I allow questions and retrieved report excerpts/metadata to
                    go to Puter and its model provider. Puter has a separate
                    account/popup. Free variants have quotas; no paid fallback.
                  </span>
                </label>
                <div className="mt-2 flex flex-wrap gap-2">
                  <button
                    disabled={!consent || busy || !model}
                    onClick={connect}
                    className="min-h-11 rounded-full bg-[#9D83E5] px-5 font-medium text-white disabled:opacity-40"
                  >
                    {busy ? "Connecting..." : "Continue to Puter"}
                  </button>
                  {sdkReady && (
                    <button
                      disabled={!consent || busy || !model}
                      onClick={authorize}
                      className="min-h-11 rounded-full border border-[#DDD3F4] px-5 text-[#8063DB] disabled:opacity-40"
                    >
                      Authorize Puter
                    </button>
                  )}
                </div>
              </>
            )}
            {error && (
              <p role="status" className="mt-2 leading-5 text-amber-800">
                {error}
              </p>
            )}
          </div>
        </div>
      )}
    </section>
  );
}
