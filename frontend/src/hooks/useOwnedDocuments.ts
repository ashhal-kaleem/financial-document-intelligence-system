"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchDocuments } from "@/lib/api";
import { useHydrated } from "@/hooks/useHydrated";
import { useFDISStore } from "@/store/useFDISStore";

export function useOwnedDocuments() {
  const hydrated = useHydrated();
  const currentUser = useFDISStore((s) => s.currentUser);
  const query = useQuery({
    queryKey: ["documents", currentUser?.id],
    queryFn: fetchDocuments,
    enabled: hydrated && Boolean(currentUser),
    refetchInterval: (q) => (q.state.data ?? []).some((d) => d.status === "queued" || d.status === "processing") ? 4000 : false,
  });
  // Never show cached account data while signed out or when the current request failed.
  const documents = hydrated && currentUser && !query.isError ? (query.data ?? []).filter((d) => !d.is_sample) : [];
  const state = !hydrated ? "loading" : !currentUser ? "signed-out" : query.isError ? "error" : query.isPending ? "loading" : documents.length ? "ready" : "empty";
  return { documents, state, retry: query.refetch };
}
