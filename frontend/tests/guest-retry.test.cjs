const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("fs");
const ts = require("typescript");

function loadApi(supabaseMock) {
  const js = ts.transpileModule(fs.readFileSync("src/lib/api.ts", "utf8"), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 },
  }).outputText;
  const mod = { exports: {} };
  new Function("require", "module", "exports", js)(
    (name) => (name === "@/lib/supabase" ? supabaseMock : require(name)),
    mod,
    mod.exports,
  );
  return mod.exports;
}

test("a 401 resets the dead guest session and retries once with the fresh token", async () => {
  let resets = 0;
  const seen = [];
  const api = loadApi({
    getAccessToken: async () => (resets ? "fresh-token" : "dead-token"),
    getSupabase: () => null,
    resetGuestSession: async () => { resets++; return { error: null }; },
  });
  global.fetch = async (url, opts) => {
    seen.push(opts.headers.Authorization);
    if (seen.length === 1) return new Response("{}", { status: 401 });
    return new Response(JSON.stringify({ data: [] }), { status: 200 });
  };
  const docs = await api.fetchDocuments();
  assert.deepEqual(docs, []);
  assert.equal(resets, 1);
  assert.deepEqual(seen, ["Bearer dead-token", "Bearer fresh-token"]);
});

test("a persistent 401 after recovery surfaces as an error, no retry loop", async () => {
  let resets = 0;
  let calls = 0;
  const api = loadApi({
    getAccessToken: async () => "token",
    getSupabase: () => null,
    resetGuestSession: async () => { resets++; return { error: null }; },
  });
  global.fetch = async () => { calls++; return new Response("{}", { status: 401 }); };
  await assert.rejects(api.fetchDocuments(), /Session could not be restored/);
  assert.equal(resets, 1);
  assert.equal(calls, 2);
});
