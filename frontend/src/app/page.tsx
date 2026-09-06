"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { DocumentSidebar } from "@/components/documents/document-sidebar";
import { ChatInterface } from "@/components/chat/chat-interface";
import { CitationDrawer } from "@/components/citations/citation-drawer";
import { fetchDocuments, deleteDocument } from "@/lib/api";
import { useHydrated } from "@/hooks/useHydrated";

export default function Home() {
  const isHydrated = useHydrated();
  const queryClient = useQueryClient();

  // TanStack Query for documents (Server State)
  const {
    data: documents = [],
    isLoading,
    isError,
    refetch,
  } = useQuery({
    queryKey: ["documents"],
    queryFn: fetchDocuments,
    enabled: isHydrated,
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: deleteDocument,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
  });

  return (
    <main className="h-screen w-screen flex overflow-hidden bg-background">
      {/* Left Sidebar */}
      <DocumentSidebar
        documents={documents}
        isLoading={!isHydrated || isLoading}
        isError={isError}
        onRetryFetch={() => refetch()}
        onDeleteDocument={(id) => deleteMutation.mutate(id)}
        onDocumentUploaded={() => {
          queryClient.invalidateQueries({ queryKey: ["documents"] });
        }}
      />

      {/* Main Chat Workspace */}
      <ChatInterface documentCount={documents.length} />

      {/* Citation Inspector Drawer */}
      <CitationDrawer />
    </main>
  );
}
