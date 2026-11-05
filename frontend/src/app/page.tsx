"use client";

import { useEffect, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ChatInterface } from "@/components/chat/chat-interface";
import { CitationDrawer } from "@/components/citations/citation-drawer";
import { PdfViewerModal } from "@/components/pdf/pdf-viewer-modal";
import { MemoExportModal } from "@/components/export/memo-export-modal";
import { AuthModal } from "@/components/auth/auth-modal";
import { UploadModal } from "@/components/documents/upload-modal";
import { OverviewScreen } from "@/components/screens/overview-screen";
import { DocumentsScreen } from "@/components/screens/documents-screen";
import { StatementsScreen } from "@/components/screens/statements-screen";
import { ComparisonScreen } from "@/components/screens/comparison-screen";
import { InsightsScreen } from "@/components/screens/insights-screen";
import { TopNav, CircleRail, LabeledRail, MobileTabNav, SampleDataTag } from "@/components/shell/app-chrome";
import { fetchDocuments, deleteDocument } from "@/lib/api";
import { useHydrated } from "@/hooks/useHydrated";
import { supabase } from "@/lib/supabase";
import { useFDISStore } from "@/store/useFDISStore";
import { cn } from "@/lib/utils";

function AppFrame({ family, children, bleed = false, sheet = "white" }: { family: string; children: React.ReactNode; bleed?: boolean; sheet?: "white" | "canvas" }) {
  return (
    <div className={cn("relative h-screen w-screen overflow-hidden", `v8-${family}`)} style={{ background: "var(--fam-canvas)" }}>
      {/* soft backdrop blobs */}
      <div className="pointer-events-none absolute -top-24 left-1/4 size-[520px] rounded-full opacity-60 blur-3xl" style={{ background: "radial-gradient(closest-side, #FFFFFF99, transparent)" }} />
      <div className="pointer-events-none absolute -bottom-40 right-0 size-[620px] rounded-full opacity-50 blur-3xl" style={{ background: "radial-gradient(closest-side, var(--fam-accent-soft), transparent)" }} />
      <div className={cn("relative z-10 flex h-full", bleed ? "p-0" : "p-4 sm:p-6")}>
        <div className={cn("flex flex-1 overflow-hidden", bleed ? "" : "rounded-[28px]")} style={{ boxShadow: "0 18px 50px #3D2E5C14", background: sheet === "canvas" ? "color-mix(in srgb, var(--fam-canvas) 24%, #FFFFFF)" : "#FFFFFF" }}>
          {children}
        </div>
      </div>
    </div>
  );
}

export default function Home() {
  const isHydrated = useHydrated();
  const queryClient = useQueryClient();
  const [, setDeletingId] = useState<string | undefined>(undefined);
  const { activeTab, setCurrentUser } = useFDISStore();

  // Keep the UI user and cached documents in step with the real Supabase session.
  useEffect(() => {
    const apply = (user: { id: string; email?: string; user_metadata?: Record<string, any> } | null | undefined) =>
      setCurrentUser(
        user
          ? { id: user.id, email: user.email, name: user.user_metadata?.full_name || user.email, avatarUrl: user.user_metadata?.avatar_url }
          : null
      );
    supabase.auth.getSession().then(({ data }) => apply(data.session?.user));
    const { data: sub } = supabase.auth.onAuthStateChange((_event, session) => {
      apply(session?.user);
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    });
    return () => sub.subscription.unsubscribe();
  }, [setCurrentUser, queryClient]);

  const { data: documents = [] } = useQuery({
    queryKey: ["documents"],
    queryFn: fetchDocuments,
    enabled: isHydrated,
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      setDeletingId(id);
      await deleteDocument(id);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["documents"] }),
    onSettled: () => setDeletingId(undefined),
  });
  void deleteMutation;

  const refreshDocs = () => queryClient.invalidateQueries({ queryKey: ["documents"] });

  return (
    <>
      {activeTab === "overview" && (
        <AppFrame family="green" sheet="canvas">
          <SampleDataTag demo={documents.length === 0} />
          <div className="flex flex-1 flex-col overflow-hidden">
            <TopNav family="green" greeting />
            <OverviewScreen />
          </div>
        </AppFrame>
      )}

      {activeTab === "chat" && (
        <AppFrame family="lilac">
          <div className="flex flex-1 flex-col overflow-hidden">
            <MobileTabNav family="lilac" />
            <ChatInterface documentCount={documents.length} onDocumentUploaded={refreshDocs} />
          </div>
        </AppFrame>
      )}

      {activeTab === "documents" && (
        <AppFrame family="green" sheet="canvas">
          <SampleDataTag demo={documents.length === 0} />
          <div className="flex flex-1 flex-col overflow-hidden">
            <TopNav family="green" />
            <div className="flex flex-1 overflow-hidden">
              <CircleRail family="green" />
              <DocumentsScreen />
            </div>
          </div>
        </AppFrame>
      )}

      {activeTab === "statements" && (
        <AppFrame family="green">
          <SampleDataTag demo={documents.length === 0} />
          <div className="flex flex-1 overflow-hidden" style={{ background: "#EAF1E4" }}>
            <LabeledRail family="green" />
            <StatementsScreen />
          </div>
        </AppFrame>
      )}

      {activeTab === "comparison" && (
        <AppFrame family="orange" sheet="canvas">
          <SampleDataTag demo={documents.length === 0} />
          <div className="flex flex-1 flex-col overflow-hidden">
            <TopNav family="orange" />
            <div className="flex flex-1 overflow-hidden">
              <CircleRail family="orange" />
              <ComparisonScreen />
            </div>
          </div>
        </AppFrame>
      )}

      {activeTab === "insights" && (
        <AppFrame family="pastel">
          <SampleDataTag demo={documents.length === 0} />
          <div className="flex flex-1 flex-col overflow-hidden">
            <MobileTabNav family="pastel" />
            <InsightsScreen />
          </div>
        </AppFrame>
      )}

      {/* Modals & Overlays */}
      <CitationDrawer />
      <PdfViewerModal />
      <MemoExportModal />
      <AuthModal />
      <UploadModal onUploaded={refreshDocs} />
    </>
  );
}
