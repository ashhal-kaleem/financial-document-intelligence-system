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

const CHAT_STORAGE_KEY = "fdis_chat_messages_v1";

export async function saveChatHistory(messages: ChatMessage[]): Promise<void> {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify(messages));
  } catch (err) {
    console.warn("Local storage save failed:", err);
  }
}

export async function loadChatHistory(): Promise<ChatMessage[]> {
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
