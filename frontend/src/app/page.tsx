/**
 * @composition Phase 14: Enterprise Assembly with Supabase Auth & Puter AI
 * @state TanStack Query (server) + Zustand (client)
 * @invariant strictly < 150 lines
 * @invariant zero raw button primitives
 */
"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { DashboardHeader } from "@/components/dashboard/dashboard-header";
import { KPIStrip } from "@/components/dashboard/kpi-strip";
import { DocumentSidebar } from "@/components/documents/document-sidebar";
import { ChatInterface } from "@/components/chat/chat-interface";
import { CitationDrawer } from "@/components/citations/citation-drawer";
import { PdfViewerModal } from "@/components/pdf/pdf-viewer-modal";
import { FinancialStatementsGrid } from "@/components/financials/financial-statements-grid";
import { FilingComparisonView } from "@/components/comparison/filing-comparison-view";
import { MemoExportModal } from "@/components/export/memo-export-modal";
import { AuthModal } from "@/components/auth/auth-modal";
import { BorderBeam } from "@/components/ui/border-beam";
import { fetchDocuments, deleteDocument } from "@/lib/api";
import { useHydrated } from "@/hooks/useHydrated";
import { useFDISStore } from "@/store/useFDISStore";

export default function Home() {
  const isHydrated = useHydrated();
  const queryClient = useQueryClient();
  const [deletingId, setDeletingId] = useState<string | undefined>(undefined);
  const { activeTab } = useFDISStore();

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

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      setDeletingId(id);
      await deleteDocument(id);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
    onSettled: () => setDeletingId(undefined),
  });

  return (
    <div className="relative h-screen w-screen flex flex-col overflow-hidden bg-background text-foreground font-sans">
      <BorderBeam
        size={140}
        duration={8}
        borderWidth={1.5}
        colorFrom="oklch(0.72 0.17 165)"
        colorTo="oklch(0.66 0.13 195)"
        className="opacity-30"
      />

      <DashboardHeader />

      <div className="flex-1 flex overflow-hidden z-10">
        <DocumentSidebar
          documents={documents}
          isLoading={!isHydrated || isLoading}
          isError={isError}
          onRetryFetch={() => refetch()}
          onDeleteDocument={(id) => deleteMutation.mutate(id)}
          deletingId={deletingId}
        />

        <main className="flex-1 flex flex-col overflow-hidden bg-card/5 backdrop-blur-sm">
          {activeTab === "chat" && (
            <>
              <div className="p-4 border-b border-border/30 bg-card/20 shrink-0">
                <KPIStrip />
              </div>
              <div className="flex-1 overflow-hidden">
                <ChatInterface
                  onDocumentUploaded={() => queryClient.invalidateQueries({ queryKey: ["documents"] })}
                  documentCount={documents.length}
                />
              </div>
            </>
          )}

          {activeTab === "statements" && <FinancialStatementsGrid />}
          {activeTab === "comparison" && <FilingComparisonView />}
        </main>

        <CitationDrawer />
      </div>

      {/* Modals & Overlays */}
      <PdfViewerModal />
      <MemoExportModal />
      <AuthModal />
    </div>
  );
}
