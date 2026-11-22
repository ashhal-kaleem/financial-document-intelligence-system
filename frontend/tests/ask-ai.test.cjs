const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("fs");
const ts = require("typescript");
function load(path, imports = {}) {
  const js = ts.transpileModule(fs.readFileSync(path, "utf8"), {
    compilerOptions: {
      module: ts.ModuleKind.CommonJS,
      target: ts.ScriptTarget.ES2020,
    },
  }).outputText;
  const mod = { exports: {} };
  new Function("require", "module", "exports", js)(
    (name) => imports[name] ?? require(name),
    mod,
    mod.exports,
  );
  return mod.exports;
}

const api = load("src/lib/api.ts", {
  "@/lib/supabase": { getAccessToken: async () => "guest-token" },
});

test("answer comes from the server endpoint with citations then answer then done", async () => {
  let request;
  global.fetch = async (url, opts) => {
    request = { url, opts };
    return new Response(
      JSON.stringify({
        data: {
          answer: "Revenue was $100 million [1].",
          citations: [
            {
              citation_id: 1,
              document_id: "d1",
              filename: "report.pdf",
              page: 2,
              chunk_index: 0,
              total_chunks: 3,
              similarity: 0.9,
              snippet: "Revenue",
            },
          ],
          chunks_count: 1,
          model: "openai/gpt-oss-120b",
        },
      }),
      { status: 200 },
    );
  };
  const events = [];
  await api.askAI("Revenue?", ["d1"], (e) => events.push(e), new AbortController().signal);
  assert.equal(request.url, "http://localhost:8000/api/v1/ask/answer");
  assert.equal(request.opts.headers.Authorization, "Bearer guest-token");
  assert.deepEqual(JSON.parse(request.opts.body).document_ids, ["d1"]);
  assert.equal(events[0].event, "citations");
  assert.equal(events[0].citations[0].filename, "report.pdf");
  assert.equal(events[1].event, "token");
  assert.equal(events[1].token, "Revenue was $100 million [1].");
  assert.equal(events[2].event, "done");
});

test("backend error message reaches the user instead of a generic failure", async () => {
  global.fetch = async () =>
    new Response(
      JSON.stringify({
        success: false,
        error: { code: "daily_question_limit", message: "Daily free question limit reached." },
      }),
      { status: 429 },
    );
  await assert.rejects(
    api.askAI("Revenue?", ["d1"], () => {}, new AbortController().signal),
    /Daily free question limit reached/,
  );
});

test("no guest session token means no answer request is sent", async () => {
  const signedOut = load("src/lib/api.ts", {
    "@/lib/supabase": { getAccessToken: async () => null },
  });
  let called = false;
  global.fetch = async () => {
    called = true;
    return new Response("{}", { status: 200 });
  };
  await assert.rejects(
    signedOut.askAI("Revenue?", ["d1"], () => {}, new AbortController().signal),
    /Sign in/,
  );
  assert.equal(called, false);
});

test("malformed answer payload is rejected, never displayed", async () => {
  global.fetch = async () =>
    new Response(JSON.stringify({ data: { citations: [] } }), { status: 200 });
  await assert.rejects(
    api.askAI("Revenue?", ["d1"], () => {}, new AbortController().signal),
    /invalid response/,
  );
});

test("end session deletes server data and reports the outcome", async () => {
  let request;
  global.fetch = async (url, opts) => {
    request = { url, opts };
    return new Response(
      JSON.stringify({
        data: { documents_deleted: 2, documents_failed: 0, identity_removed: true },
      }),
      { status: 200 },
    );
  };
  const out = await api.endSession();
  assert.equal(request.url, "http://localhost:8000/api/v1/session");
  assert.equal(request.opts.method, "DELETE");
  assert.equal(out.documents_deleted, 2);
  assert.equal(out.identity_removed, true);
});

test("failed session cleanup is not reported as success", async () => {
  global.fetch = async () => new Response("{}", { status: 500 });
  await assert.rejects(api.endSession(), /Session cleanup failed/);
});
