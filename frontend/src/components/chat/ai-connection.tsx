"use client";
import { useState, useEffect } from 'react';
import { loadPuter, PUTER_MODELS } from '@/lib/puter-ai';
import { useFDISStore } from '@/store/useFDISStore';

export function AIConnection({connected, setConnected, model, setModel}: {
  connected: boolean; setConnected: (v: boolean) => void; model: string; setModel: (v: string) => void;
}) {
  const owner = useFDISStore(s => s.currentUser?.id);
  const [sdkReady, setSDKReady] = useState(false);
  const [consent, setConsent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  useEffect(() => { setConsent(false); setConnected(false); setError(''); }, [owner, setConnected]);
  const connect = async () => {
    if (!owner) { useFDISStore.getState().setAuthModalOpen(true); return; }
    if (!consent) return;
    setBusy(true); setError('');
    try {
      const sdk = await loadPuter();
      setSDKReady(true);
      // Popup must be initiated by a click. A second explicit click after script loading preserves it.
      if (!sdk.auth.isSignedIn()) { setError('AI connection loaded. Click Authorize Puter to open its popup.'); return; }
      if (useFDISStore.getState().currentUser?.id === owner) setConnected(true);
    } catch { if (useFDISStore.getState().currentUser?.id === owner) setError('AI connection could not load. Retry.'); }
    finally { setBusy(false); }
  };
  const authorize = async () => {
    if (!window.puter || !owner || !consent) return;
    setBusy(true); setError('');
    try {
      await window.puter.auth.signIn();
      if (useFDISStore.getState().currentUser?.id === owner) setConnected(true);
    } catch { if (useFDISStore.getState().currentUser?.id === owner) setError('Puter connection was cancelled or failed. No question was sent.'); }
    finally { setBusy(false); }
  };
  return <section className="shrink-0 border-b border-[#ECE8F6] bg-white px-5 py-3 text-xs">
    <div className="flex flex-wrap items-center gap-3">
      <strong>Workspace AI {connected ? '· Puter connected' : '· not connected'}</strong>
      <label className="flex flex-wrap items-center gap-2">Model
        <select value={model} onChange={e => setModel(e.target.value)} className="min-h-10 max-w-full rounded border border-[#ECE8F6] bg-white px-2" aria-label="AI model">
          <option value="">Choose a free model</option>
          {PUTER_MODELS.map(m => <option key={m.id} value={m.id}>{m.name}</option>)}
        </select>
      </label>
      {connected && <button className="min-h-10 rounded border px-3" onClick={() => { window.puter?.auth.signOut(); setConnected(false); setConsent(false); }}>Disconnect AI</button>}
    </div>
    {!connected && <>
      <details className="mt-2"><summary className="min-h-10 cursor-pointer py-2 underline">What is shared, costs and privacy</summary>
      <div className="max-h-44 overflow-y-auto pr-1">
      <p className="leading-5">Questions, retrieved report excerpts, filenames and page metadata go to Puter and the selected model provider when you ask. The original PDF and FDIS token are not sent. Review confidential report permissions first.</p>
      <p className="mt-1 leading-5 text-[#6E6A78]">Connecting loads Puter's third-party SDK. AI use is metered to your Puter account; limits or other account charges may still apply. Cancelling stops waiting, but a model request already sent may finish and be billed. Answers appear after completion and citation-ID checks, not token by token. Citations are checked for valid IDs, not semantic truth. <a className="underline" href="https://puter.com/privacy" target="_blank" rel="noreferrer">Puter privacy</a> · <a className="underline" href="https://docs.puter.com/rate-limits-and-quotas/" target="_blank" rel="noreferrer">Limits</a></p>
      </div></details>
      <label className="flex min-h-10 items-start gap-2 py-2 leading-5"><input className="mt-1 size-4 shrink-0" type="checkbox" checked={consent} onChange={e => setConsent(e.target.checked)} /><span>I allow questions and retrieved report excerpts/metadata to go to Puter and its model provider. Puter has a separate account/popup. Free variants have quotas; no paid fallback.</span></label>
      <div className="mt-2 flex flex-wrap gap-2">
        <button disabled={!consent || busy || !model} onClick={connect} className="min-h-10 rounded bg-[#141414] px-4 text-white disabled:opacity-40">{busy ? 'Connecting…' : 'Connect AI'}</button>
        {sdkReady && <button disabled={!consent || busy || !model} onClick={authorize} className="min-h-10 rounded border px-4 disabled:opacity-40">Authorize Puter</button>}
      </div>
    </>}
    {error && <p role="status" className="mt-2 leading-5 text-amber-800">{error}</p>}
  </section>;
}
