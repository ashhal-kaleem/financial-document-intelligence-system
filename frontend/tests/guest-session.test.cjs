const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("fs");
const ts = require("typescript");

process.env.NEXT_PUBLIC_SUPABASE_URL = "http://localhost:54321";
process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY = "test-anon-key";

function loadSupabase(authMock) {
  const js = ts.transpileModule(fs.readFileSync("src/lib/supabase.ts", "utf8"), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 },
  }).outputText;
  const mod = { exports: {} };
  new Function("require", "module", "exports", js)(
    (name) => (name === "@supabase/supabase-js" ? { createClient: () => ({ auth: authMock }) } : require(name)),
    mod,
    mod.exports,
  );
  return mod.exports;
}

function makeAuth(existingSession, calls) {
  return {
    getSession: async () => ({ data: { session: existingSession } }),
    signOut: async () => { calls.push("signOut"); },
    signInAnonymously: async () => { calls.push("signInAnonymously"); return { error: null }; },
  };
}

test("guest session: an existing anonymous session is reused as-is", async () => {
  const calls = [];
  const supabase = loadSupabase(makeAuth({ user: { is_anonymous: true } }, calls));
  const { error } = await supabase.ensureGuestSession();
  assert.equal(error, null);
  assert.deepEqual(calls, []);
});

test("guest session: a persisted named (Google) login is never reused", async () => {
  const calls = [];
  const supabase = loadSupabase(makeAuth({ user: { is_anonymous: false } }, calls));
  const { error } = await supabase.ensureGuestSession();
  assert.equal(error, null);
  assert.deepEqual(calls, ["signOut", "signInAnonymously"]);
});

test("guest session: no session starts an anonymous sign-in", async () => {
  const calls = [];
  const supabase = loadSupabase(makeAuth(null, calls));
  const { error } = await supabase.ensureGuestSession();
  assert.equal(error, null);
  assert.deepEqual(calls, ["signInAnonymously"]);
});
