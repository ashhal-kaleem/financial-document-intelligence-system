/**
 * @source @supabase/supabase-js
 * @client Browser Supabase Client for Authentication & Row Level Security
 * @invariant Strictly < 150 lines
 */
import { safeReturnPath } from "@/lib/workspace-routes";
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

export async function signInWithGoogle(): Promise<{ error: Error | null }> {
  const supabase = getSupabase();
  if (!supabase)
    return {
      error: new Error("Sign-in is not configured for this deployment."),
    };
  try {
    // Public provider settings prevent sending people to a known-disabled provider error page.
    const settings = await fetch(`${supabaseUrl}/auth/v1/settings`, {
      headers: { apikey: supabaseAnonKey as string },
      signal: AbortSignal.timeout(10000),
    });
    if (!settings.ok)
      return {
        error: new Error("Sign-in service is unavailable. Retry shortly."),
      };
    const providers = await settings.json();
    if (providers.external?.google !== true)
      return {
        error: new Error(
          "Google sign-in is not enabled yet. Your workspace has not been opened. Please try again after setup is complete.",
        ),
      };
    const { error } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: {
        redirectTo:
          typeof window !== "undefined"
            ? window.location.origin +
              safeReturnPath(window.location.pathname + window.location.search)
            : undefined,
      },
    });
    return { error: error ? new Error(error.message) : null };
  } catch (err: any) {
    return { error: err };
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
