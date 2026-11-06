const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
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
const history = load("src/lib/chat-history.ts");
const api = load("src/lib/api.ts", {
  "@/lib/supabase": { getAccessToken: async () => "test-token" },
});
test("history is account-scoped and never claims legacy unscoped messages", async () => {
  global.window = {};
  const data = new Map([
    ["fdis_chat_messages_v1", '[{"content":"legacy private data"}]'],
  ]);
  global.localStorage = {
    getItem: (k) => data.get(k),
    setItem: (k, v) => data.set(k, v),
    removeItem: (k) => data.delete(k),
  };
  assert.deepEqual(await history.loadChatHistory("alice"), []);
  assert.equal(data.has("fdis_chat_messages_v1"), false);
  const messages = [{ id: "1", role: "user", content: "alice report" }];
  await history.saveChatHistory(messages, "alice");
  assert.deepEqual(await history.loadChatHistory("bob"), []);
  assert.deepEqual(await history.loadChatHistory(), []);
  assert.deepEqual(await history.loadChatHistory("alice"), messages);
  await history.saveChatHistory(messages);
  assert.equal(data.size, 1);
});
function mockStream(text) {
  global.fetch = async () =>
    new Response(
      new ReadableStream({
        start(c) {
          // Deliberately split inside JSON and UTF-8 bytes.
          const bytes = new TextEncoder().encode(text);
          for (let i = 0; i < bytes.length; i += 7)
            c.enqueue(bytes.slice(i, i + 7));
          c.close();
        },
      }),
      { status: 200 },
    );
}
test("stream accepts only a complete answer and terminal marker", async () => {
  mockStream(
    'data: {"event":"token","token":"₹42 [1]"}\n\ndata: {"event":"done"}\n\ndata: [DONE]\n\n',
  );
  const events = [];
  await api.streamQuestion("question", [], undefined, (e) => events.push(e));
  assert.equal(events[0].token, "₹42 [1]");
  assert.equal(events.at(-1).event, "done");
});
for (const [name, text] of Object.entries({
  provider_error:
    'data: {"event":"error","detail":"failed"}\n\ndata: [DONE]\n\n',
  missing_done: "data: [DONE]\n\n",
  truncated: 'data: {"event":"token","token":"partial"}\n\n',
  no_terminal: 'data: {"event":"done"}\n\n',
  malformed: "data: {invalid}\n\n",
}))
  test(`stream rejects ${name}`, async () => {
    mockStream(text);
    await assert.rejects(api.streamQuestion("question", []));
  });
test("callback failures propagate rather than being swallowed", async () => {
  mockStream('data: {"event":"token","token":"x"}\n\n');
  await assert.rejects(
    api.streamQuestion("q", [], undefined, () => {
      throw Error("callback failure");
    }),
    /callback failure/,
  );
});
test("failed deletion is not reported as success", async () => {
  global.fetch = async () => new Response("{}", { status: 500 });
  await assert.rejects(api.deleteDocument("id"), /Delete failed/);
});

test("account switch clears document, citation and modal state", () => {
  const { useFDISStore: store } = load("src/store/useFDISStore.ts");
  store.getState().setCurrentUser({ id: "alice" });
  store.getState().setChatDraft("secret-doc", "private draft");
  store
    .getState()
    .setSelectedDocument({ id: "secret-doc", filename: "private.pdf" });
  store
    .getState()
    .openPdfViewer({
      documentId: "secret-doc",
      filename: "private.pdf",
      pageNumber: 2,
    });
  store.getState().setUploadOpen(true);
  store.getState().setCurrentUser({ id: "bob" });
  const state = store.getState();
  assert.deepEqual(state.chatDrafts, {});
  assert.equal(state.selectedDocument, null);
  assert.equal(state.activeCitation, null);
  assert.equal(state.pdfViewer.isOpen, false);
  assert.equal(state.pdfViewer.documentId, undefined);
  assert.equal(state.isUploadOpen, false);
});

function ownedState({
  owner = "alice",
  hydrated = true,
  data = [],
  pending = false,
  error = false,
} = {}) {
  return load("src/hooks/useOwnedDocuments.ts", {
    "@tanstack/react-query": {
      useQuery: () => ({
        data,
        isError: error,
        isPending: pending,
        refetch() {},
      }),
    },
    "@/lib/api": { fetchDocuments() {} },
    "@/hooks/useHydrated": { useHydrated: () => hydrated },
    "@/store/useFDISStore": {
      useFDISStore: (select) =>
        select({ currentUser: owner ? { id: owner } : null }),
    },
  }).useOwnedDocuments();
}
test("document state distinguishes signed-out, loading, error and true empty results", () => {
  const privateDoc = { id: "private", filename: "private.pdf" };
  for (const props of [{ owner: null }, { hydrated: false }, { error: true }]) {
    assert.deepEqual(
      ownedState({ ...props, data: [privateDoc] }).documents,
      [],
    );
  }
  assert.equal(ownedState({ owner: null }).state, "signed-out");
  assert.equal(ownedState({ pending: true }).state, "loading");
  assert.equal(ownedState({ error: true }).state, "error");
  assert.equal(ownedState().state, "empty");
  assert.deepEqual(
    ownedState({ data: [privateDoc, { id: "sample", is_sample: true }] })
      .documents,
    [privateDoc],
  );
});
test("production screens contain no seeded financial records or fake activity fallback", () => {
  const paths = fs
    .readdirSync("src/components/screens")
    .map((p) => "src/components/screens/" + p);
  const source = paths.map((p) => fs.readFileSync(p, "utf8")).join("\n");
  assert.doesNotMatch(
    source,
    /AAPL|MSFT|TSLA|391\.0B|FY2024|Questions This Week|SampleDataTag/,
  );
  assert.equal(fs.existsSync("src/mocks"), false);
  assert.doesNotMatch(
    fs.readFileSync("src/components/shell/app-chrome.tsx", "utf8"),
    /BellButton|SampleDataTag/,
  );
  assert.doesNotMatch(
    fs.readFileSync("src/components/citations/citation-drawer.tsx", "utf8"),
    /Evidence passage verified/,
  );
});

test("real routes, canonical tab links and safe auth return paths", () => {
  const { TAB_PATHS, tabForPath, safeReturnPath } = load(
    "src/lib/workspace-routes.ts",
  );
  for (const [tab, path] of Object.entries(TAB_PATHS)) {
    assert.equal(tabForPath(path), tab);
    assert.equal(fs.existsSync(`src/app/(workspace)${path}/page.tsx`), true);
  }
  for (const invalid of [
    "https://evil.invalid",
    "//evil.invalid",
    "/unknown",
    "javascript:alert(1)",
  ])
    assert.equal(safeReturnPath(invalid), "/workspace");
  assert.equal(
    safeReturnPath("/qa?question=private&access_token=secret"),
    "/qa",
  );
  const id = "12345678-1234-1234-1234-123456789abc";
  assert.equal(safeReturnPath("/qa?document=" + id), "/qa?document=" + id);
  assert.doesNotMatch(
    fs.readFileSync("src/store/useFDISStore.ts", "utf8"),
    /activeTab:|setActiveTab:/,
  );
  assert.match(
    fs.readFileSync("src/components/shell/app-chrome.tsx", "utf8"),
    /href=\{TAB_PATHS\[item.id\]\}/,
  );
});
test("history separates documents and clear persists", async () => {
  const data = new Map();
  global.window = {};
  global.localStorage = {
    getItem: (k) => data.get(k),
    setItem: (k, v) => data.set(k, v),
    removeItem: (k) => data.delete(k),
  };
  const m = [{ id: "x", role: "user", content: "private" }];
  await history.saveChatHistory(m, "alice", "one");
  assert.deepEqual(await history.loadChatHistory("alice", "two"), []);
  assert.deepEqual(await history.loadChatHistory("bob", "one"), []);
  await history.saveChatHistory([], "alice", "one");
  assert.deepEqual(await history.loadChatHistory("alice", "one"), []);
});
test("Q&A has explicit document scope, no pre-accept draft deletion, and no no-op controls", () => {
  const chat = fs.readFileSync(
    "src/components/chat/chat-interface.tsx",
    "utf8",
  );
  assert.match(chat, /askPuter\(\s*content,\s*\[document.id\]/);
  assert.match(chat, /Back to documents/);
  assert.match(chat, /Cancel answer/);
  assert.doesNotMatch(
    fs.readFileSync("src/components/chat/chat-input-box.tsx", "utf8"),
    /setDraft\(""\)/,
  );
  assert.doesNotMatch(chat, /MoreHorizontal|Export memo|Export chat/);
});
test("disabled Google provider stays in app without starting OAuth", async () => {
  let oauthCalls = 0;
  const client = {
    auth: {
      signInWithOAuth: async () => {
        oauthCalls++;
        return { error: null };
      },
    },
  };
  const auth = load("src/lib/supabase.ts", {
    "@/lib/workspace-routes": { safeReturnPath: (p) => p },
    "@supabase/supabase-js": { createClient: () => client },
  });
  // This test module reads env at initialization, so reload after configuring the synthetic project.
  process.env.NEXT_PUBLIC_SUPABASE_URL = "https://fixture.invalid";
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY = "fixture";
  const configured = load("src/lib/supabase.ts", {
    "@/lib/workspace-routes": { safeReturnPath: (p) => p },
    "@supabase/supabase-js": { createClient: () => client },
  });
  global.fetch = async () =>
    new Response(JSON.stringify({ external: { google: false } }), {
      status: 200,
    });
  const { error } = await configured.signInWithGoogle();
  assert.match(error.message, /not enabled/);
  assert.equal(oauthCalls, 0);
  delete process.env.NEXT_PUBLIC_SUPABASE_URL;
  delete process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
});
test("one New conversation control, chosen rounded top navigation and Back path stay intact", () => {
  const chrome = fs.readFileSync("src/components/shell/app-chrome.tsx", "utf8");
  const chat = fs.readFileSync(
    "src/components/chat/chat-interface.tsx",
    "utf8",
  );
  assert.doesNotMatch(chrome, />\s*New conversation\s*<\/button>/);
  assert.equal((chat.match(/>\s*New conversation\s*<\/button>/g) || []).length, 1);
  assert.match(chrome, /aria-label="Workspace"/);
  assert.match(chrome, /rounded-full/);
  assert.match(chrome, /bg-\[#CDEFA6\]/);
  assert.match(chat, /href="\/documents"[^>]*>\s*← Back to documents/);
  assert.match(chrome, /if \(!user\) return null/);
});

test("production has no deleted backend rewrite and removed features have no state", async () => {
  const config = (await import("../next.config.mjs")).default;
  const before = process.env.NODE_ENV;
  try {
    process.env.NODE_ENV = "production";
    assert.deepEqual(await config.rewrites(), []);
    process.env.NODE_ENV = "development";
    assert.equal(
      (await config.rewrites())[0].destination,
      "http://127.0.0.1:8000/api/v1/:path*",
    );
  } finally {
    process.env.NODE_ENV = before;
  }
  const state = load("src/store/useFDISStore.ts").useFDISStore.getState();
  assert.equal("isExportModalOpen" in state, false);
  assert.equal("isSidebarCollapsed" in state, false);
});
test("retired frontend source and assets are absent, required framework packages remain", () => {
  for (const p of [
    "src/components/export/memo-export-modal.tsx",
    "src/lib/sound.ts",
    "mocks/seeds/filings.json",
    "public/videos/hero-bg.mp4",
  ])
    assert.equal(fs.existsSync(p), false);
  assert.equal(fs.existsSync("src/app/icon.svg"), true);
  const pkg = JSON.parse(fs.readFileSync("package.json", "utf8"));
  assert.ok(pkg.dependencies["react-dom"]);
  assert.equal(pkg.dependencies["next"], "15.5.28");
  assert.equal(pkg.dependencies["motion"], undefined);
  assert.equal(pkg.pnpm.overrides["next>postcss"], "8.5.32");
});
