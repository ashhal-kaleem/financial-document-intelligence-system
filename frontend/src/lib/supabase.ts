/**
 * @source @supabase/supabase-js
 * @client Browser Supabase Client for Authentication & Row Level Security
 * @invariant Strictly < 150 lines
 */
import { createClient, type SupabaseClient } from "@supabase/supabase-js";

// No hardcoded project: sign-in works only when these are set (see frontend/.env.example).
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

export const isAuthConfigured = Boolean(supabaseUrl && supabaseAnonKey);

let client: SupabaseClient | null = null;
/**
 * The browser client, or null when Supabase is not configured.
 * Auth state lives in sessionStorage: it survives a reload inside the same
 * tab, but a closed tab is gone forever. A reopened tab is always a fresh
 * private guest. (Browsers may still resurrect sessionStorage via
 * "reopen closed tab" or full session restore; that is a browser feature,
 * not something the app controls.)
 */
export function getSupabase(): SupabaseClient | null {
  if (!isAuthConfigured) return null;
  if (!client)
    client = createClient(supabaseUrl as string, supabaseAnonKey as string, {
      auth: {
        storage:
          typeof window !== "undefined" ? window.sessionStorage : undefined,
        persistSession: true,
        autoRefreshToken: true,
      },
    });
  return client;
}

/** Drop any legacy persisted login (e.g. an old Google session saved in
 * localStorage before the app went guest-only) so it can never resume. */
export function clearLegacyPersistedSession(): void {
  if (typeof window === "undefined") return;
  try {
    for (const key of Object.keys(window.localStorage)) {
      if (key.startsWith("sb-") && key.endsWith("-auth-token"))
        window.localStorage.removeItem(key);
    }
  } catch {
    // Storage may be unavailable (blocked cookies); nothing to clear.
  }
}

let inFlight: Promise<{ error: Error | null }> | null = null;

/** Start (or reuse) this tab's private guest session. Concurrent callers share
 * one sign-in so a fresh tab can never create duplicate guest identities. */
export function ensureGuestSession(): Promise<{ error: Error | null }> {
  if (!inFlight)
    inFlight = _ensureGuestSession().finally(() => {
      inFlight = null;
    });
  return inFlight;
}

async function _ensureGuestSession(): Promise<{ error: Error | null }> {
  const supabase = getSupabase();
  if (!supabase)
    return {
      error: new Error("Guest sessions are not configured for this deployment."),
    };
  try {
    clearLegacyPersistedSession();
    const { data } = await supabase.auth.getSession();
    const existing = data.session;
    // Same tab, session already live: reuse it (survives a page reload).
    if (existing?.user?.is_anonymous) return { error: null };
    // A named (Google) login is never reused: the app is guest-only. Old
    // account data stays private in Supabase; it is simply not shown here.
    if (existing) await supabase.auth.signOut();
    const { error } = await supabase.auth.signInAnonymously();
    return { error: error ? new Error(error.message) : null };
  } catch (err: any) {
    return { error: err instanceof Error ? err : new Error(String(err)) };
  }
}

/** Recover from a dead guest identity (expired/swept server-side): drop the
 * stale session and start a fresh anonymous one. Only ever called after the
 * backend has already rejected the old identity, so no data is reachable. */
export async function resetGuestSession(): Promise<{ error: Error | null }> {
  const supabase = getSupabase();
  if (!supabase)
    return {
      error: new Error("Guest sessions are not configured for this deployment."),
    };
  try {
    await supabase.auth.signOut();
  } catch {
    // A stale session may fail to sign out; it is unusable either way.
  }
  return ensureGuestSession();
}

export async function signOutUser(): Promise<void> {
  const result = await getSupabase()?.auth.signOut();
  if (result?.error) throw new Error("Sign out failed.");
}

export async function getAccessToken(): Promise<string | null> {
  const { data } = (await getSupabase()?.auth.getSession()) ?? { data: null };
  return data?.session?.access_token || null;
}

export async function getSessionUser() {
  const { data } = (await getSupabase()?.auth.getUser()) ?? { data: null };
  return data?.user || null;
}
