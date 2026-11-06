import { getAccessToken } from "@/lib/supabase";
import type { StreamEventPayload, CitationItem } from "@/lib/api";

export const PUTER_MODELS = [
  {
    id: "openrouter:google/gemma-4-31b-it:free",
    name: "Gemma 4 31B · free variant",
  },
  { id: "infron:qwen/qwen3.8-27b:free", name: "Qwen 3.8 27B · free variant" },
  {
    id: "openrouter:nvidia/nemotron-3.5-lightning:free",
    name: "Nemotron 3.5 Lightning · free variant",
  },
];
interface Puter {
  auth: { signIn(): Promise<unknown>; isSignedIn(): boolean; signOut(): void };
  ai: {
    chat(
      messages: { role: string; content: string }[],
      options: Record<string, unknown>,
    ): Promise<{
      message?: { content?: string };
      finish_reason?: string;
      error?: unknown;
      usage?: { cost?: number };
    }>;
  };
}
declare global {
  interface Window {
    puter?: Puter;
  }
}
let loading: Promise<Puter> | null = null;
export async function loadPuter(): Promise<Puter> {
  if (window.puter) return window.puter;
  if (!loading)
    loading = new Promise((resolve, reject) => {
      const script = document.createElement("script");
      script.src = "https://js.puter.com/v2/";
      script.async = true;
      const timeout = setTimeout(() => {
        loading = null;
        script.remove();
        reject(Error("AI connection timed out."));
      }, 15000);
      script.onload = () => {
        clearTimeout(timeout);
        if (window.puter) resolve(window.puter);
        else {
          loading = null;
          reject(Error("AI SDK unavailable."));
        }
      };
      script.onerror = () => {
        clearTimeout(timeout);
        loading = null;
        script.remove();
        reject(Error("Could not load AI connection."));
      };
      document.head.appendChild(script);
    });
  return loading;
}
const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
async function post(path: string, body: unknown, signal?: AbortSignal) {
  const token = await getAccessToken();
  if (!token) throw Error("Sign in to continue.");
  const response = await fetch(`${API_BASE}/ask/${path}`, {
    method: "POST",
    signal,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(body),
  });
  if (!response.ok)
    throw Error(
      path === "browser-context"
        ? "AI context or free model is unavailable. No paid fallback was used."
        : "Answer citation checks failed.",
    );
  return (await response.json()).data;
}

export async function askPuter(
  question: string,
  documentIds: string[],
  model: string,
  onEvent: (event: StreamEventPayload) => void,
  signal: AbortSignal,
): Promise<void> {
  if (!PUTER_MODELS.some((m) => m.id === model))
    throw Error("Model not enabled.");
  const sdk = window.puter;
  if (!sdk?.auth.isSignedIn()) throw Error("Connect your AI account first.");
  const context: {
    messages: { role: string; content: string }[];
    citations: CitationItem[];
    receipt: string | null;
    answer?: string;
  } = await post(
    "browser-context",
    {
      question,
      document_ids: documentIds.length ? documentIds : null,
      model,
      consent: true,
    },
    signal,
  );
  if (signal.aborted) throw Error("Cancelled");
  if (context.answer) {
    onEvent({ event: "token", token: context.answer });
    onEvent({ event: "done" });
    return;
  }
  // Use one normalized non-streamed result so a clean finish reason is required.
  // Streaming chunks lack a stable terminal finish marker across providers.
  const timeoutSignal = AbortSignal.timeout(120000);
  const providerSignal = AbortSignal.any([signal, timeoutSignal]);
  const result = await sdk.ai.chat(context.messages, {
    model,
    provider: model.split(":")[0],
    fallback: false,
    stream: false,
    normalize: true,
    max_tokens: 1024,
    temperature: 0.1,
    signal: providerSignal,
  });
  const answer = result.message?.content;
  if (
    result.error ||
    result.finish_reason !== "stop" ||
    typeof answer !== "string" ||
    !answer ||
    answer.length > 60000 ||
    signal.aborted ||
    !context.receipt
  )
    throw Error(
      "AI did not return a complete text answer with a supported finish reason. Nothing was accepted; check the provider or retry.",
    );
  // A runtime charge is a safety failure, never silently accepted as a free answer.
  if (result.usage?.cost === undefined || result.usage.cost !== 0)
    throw Error(
      "AI did not confirm zero model cost. Disconnect and review Puter usage.",
    );
  await post("browser-validate", { receipt: context.receipt, answer }, signal);
  if (signal.aborted) throw Error("Cancelled");
  onEvent({ event: "citations", citations: context.citations });
  onEvent({ event: "token", token: answer });
  onEvent({ event: "done" });
}
