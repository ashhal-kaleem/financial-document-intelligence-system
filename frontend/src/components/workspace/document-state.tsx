"use client";

import { useFDISStore } from "@/store/useFDISStore";

export function DocumentState({
  state,
  retry,
  hideUpload = false,
}: {
  state: string;
  retry: () => unknown;
  hideUpload?: boolean;
}) {
  const { setAuthModalOpen, setUploadOpen } = useFDISStore();
  if (state === "ready") return null;
  return (
    <section className="rounded-[22px] bg-white p-6 sm:p-8" aria-live="polite">
      <h2 className="text-xl font-medium fam-ink">
        {state === "signed-out"
          ? "Your private workspace"
          : state === "error"
            ? "Documents could not be loaded"
            : state === "loading"
              ? "Loading your documents"
              : "No documents yet"}
      </h2>
      <p className="mt-3 max-w-xl text-sm leading-6 fam-sub">
        {state === "signed-out"
          ? "Sign in to see your documents. No account data is shown while signed out."
          : state === "error"
            ? "The request failed. Your library may contain documents; this is not an empty-library result. On Free hosting the server may be waking up. Retry to check; sign in again if your session expired."
            : state === "loading"
              ? "Loading your private library. Free hosting can take longer to start; this request will show a retry option if it takes too long."
              : "Upload a PDF to start. Only your uploaded documents will appear here."}
      </p>
      {state !== "loading" && !(state === "empty" && hideUpload) && (
        <button
          onClick={() =>
            state === "signed-out"
              ? setAuthModalOpen(true)
              : state === "error"
                ? retry()
                : setUploadOpen(true)
          }
          className="mt-5 rounded-full bg-[#0C3B2E] px-5 py-2.5 text-sm font-medium text-white"
        >
          {state === "signed-out"
            ? "Sign in"
            : state === "error"
              ? "Retry"
              : "Upload PDF"}
        </button>
      )}
      {state === "error" && (
        <button
          onClick={() => setAuthModalOpen(true)}
          className="ml-3 mt-4 min-h-11 underline text-sm"
        >
          Check sign-in
        </button>
      )}
    </section>
  );
}
