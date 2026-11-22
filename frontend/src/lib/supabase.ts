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
/** The browser client, or null when Supabase is not configured. */
export function getSupabase(): SupabaseClient | null {
  if (!isAuthConfigured) return null;
  if (!client)
    client = createClient(supabaseUrl as string, supabaseAnonKey as string);
  return client;
}

/** Start (or reuse) this visitor's private guest session. No login is ever shown. */
export async function ensureGuestSession(): Promise<{ error: Error | null }> {
  const supabase = getSupabase();
  if (!supabase)
    return {
      error: new Error("Guest sessions are not configured for this deployment."),
    };
  try {
    const { data } = await supabase.auth.getSession();
    if (data.session) return { error: null };
    const { error } = await supabase.auth.signInAnonymously();
    return { error: error ? new Error(error.message) : null };
  } catch (err: any) {
    return { error: err instanceof Error ? err : new Error(String(err)) };
  }
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
