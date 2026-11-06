/**
 * Chat history kept in this browser only (localStorage).
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
function storageKey(ownerId: string) { return CHAT_STORAGE_KEY + ownerId; }

export async function saveChatHistory(messages: ChatMessage[], ownerId?: string): Promise<void> {
  if (typeof window === "undefined" || !ownerId) return;
  try {
    localStorage.removeItem("fdis_chat_messages_v1"); // Unscoped legacy history cannot safely be assigned to any user.
    localStorage.setItem(storageKey(ownerId), JSON.stringify(messages));
  } catch (err) {
    console.warn("Local storage save failed:", err);
  }
}

export async function loadChatHistory(ownerId?: string): Promise<ChatMessage[]> {
  if (typeof window === "undefined" || !ownerId) return [];
  try {
    localStorage.removeItem("fdis_chat_messages_v1");
    const raw = localStorage.getItem(storageKey(ownerId));
    if (raw && typeof raw === "string") {
      const parsed = JSON.parse(raw);
      return Array.isArray(parsed) ? parsed : [];
    }
  } catch (err) {
    console.warn("Local storage read failed:", err);
  }
  return [];
}
