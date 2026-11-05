/**
 * @source @heyputer/puter.js SDK (Client-Side Cloud Engine)
 * @capabilities AI Chat (Claude 3.5 Sonnet / GPT-4o), Audio TTS, KV Storage, FS Document Staging
 * @invariant Zero Server API Keys Required
 * @invariant Strictly < 150 lines
 */
"use client";

// Puter is a browser-only SDK. Lazy-load it so the module never enters the
// server bundle (a top-level import breaks production SSR with
// "TypeError: handler is not a function").
type Puter = (typeof import("@heyputer/puter.js"))["puter"];
let puterPromise: Promise<Puter> | null = null;
function getPuter(): Promise<Puter> {
  if (!puterPromise) {
    puterPromise = import("@heyputer/puter.js").then((m) => {
      const p = m.puter as Puter;
      try {
        (p as any).quiet = true;
      } catch {
        // non-fatal
      }
      return p;
    });
  }
  return puterPromise;
}

export interface PuterChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: any[];
  timestamp?: string;
  model?: string;
}

export async function streamPuterChat(
  messages: Array<{ role: string; content: string }>,
  model: string = "claude-3-5-sonnet",
  onToken: (token: string) => void
): Promise<string> {
  let fullText = "";
  try {
    const puter = await getPuter();
    const stream = await puter.ai.chat(messages, {
      model: model || "claude-3-5-sonnet",
      stream: true,
    });

    for await (const chunk of stream as any) {
      const token = chunk?.text || chunk?.message?.content || "";
      if (token && typeof token === "string") {
        fullText += token;
        onToken(token);
      }
    }
  } catch (err: any) {
    // Graceful fallback to non-streaming if provider stream fails
    const puter2 = await getPuter();
    const res = (await puter2.ai.chat(messages, { model: model || "claude-3-5-sonnet" })) as any;
    let content = "";
    if (typeof res === "string") {
      content = res;
    } else if (typeof res?.message?.content === "string") {
      content = res.message.content;
    } else if (Array.isArray(res?.message?.content)) {
      content = res.message.content.map((c: any) => c?.text || "").join("");
    } else {
      content = String(res || "");
    }
    fullText = content;
    onToken(content);
  }
  return fullText;
}

export async function speakFinancialBriefing(text: string): Promise<HTMLAudioElement | null> {
  try {
    const cleanText = text.replace(/\[\d+\]/g, "").slice(0, 500);
    const puter3 = await getPuter();
    const audio = await puter3.ai.txt2speech(cleanText, {
      engine: "openai",
      voice: "alloy",
    });
    if (audio) {
      audio.play();
      return audio;
    }
  } catch (err) {
    console.warn("Puter TTS audio synthesis fallback:", err);
  }
  return null;
}

const CHAT_STORAGE_KEY = "fdis_chat_messages_v1";

export async function saveChatHistory(messages: PuterChatMessage[]): Promise<void> {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify(messages));
  } catch (err) {
    console.warn("Local storage save failed:", err);
  }
}

export async function loadChatHistory(): Promise<PuterChatMessage[]> {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(CHAT_STORAGE_KEY);
    if (raw && typeof raw === "string") {
      return JSON.parse(raw);
    }
  } catch (err) {
    console.warn("Local storage read failed:", err);
  }
  return [];
}
