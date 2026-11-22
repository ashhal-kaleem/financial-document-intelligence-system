/**
 * Chat history kept in this tab only (sessionStorage). Closing the tab
 * discards it; legacy localStorage entries are wiped on first use.
 */
"use client";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: any[];
  timestamp?: string;
  model?: string;
}

const CHAT_STORAGE_KEY = "fdis_chat_messages_v2:";
/** Remove every chat-history entry ever written to persistent storage. */
function wipeLegacy(): void {
  try {
    for (const key of Object.keys(window.localStorage)) {
      if (key.startsWith("fdis_chat_messages_")) window.localStorage.removeItem(key);
    }
  } catch {
    // Storage may be unavailable; nothing else to do.
  }
}
function storageKey(ownerId: string, scope?: string) {
  return CHAT_STORAGE_KEY + ownerId + (scope ? ":doc:" + scope : "");
}

export async function saveChatHistory(
  messages: ChatMessage[],
  ownerId?: string,
  scope?: string,
): Promise<void> {
  if (typeof window === "undefined" || !ownerId) return;
  try {
    wipeLegacy();
    sessionStorage.setItem(storageKey(ownerId, scope), JSON.stringify(messages));
  } catch (err) {
    console.warn("Local storage save failed:", err);
  }
}

export async function loadChatHistory(
  ownerId?: string,
  scope?: string,
): Promise<ChatMessage[]> {
  if (typeof window === "undefined" || !ownerId) return [];
  try {
    wipeLegacy();
    const raw = sessionStorage.getItem(storageKey(ownerId, scope));
    if (raw && typeof raw === "string") {
      const parsed = JSON.parse(raw);
      return Array.isArray(parsed) ? parsed : [];
    }
  } catch (err) {
    console.warn("Local storage read failed:", err);
  }
  return [];
}
