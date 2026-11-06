"use client";
import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { usePathname } from "next/navigation";
import { TopNav } from "@/components/shell/app-chrome";
import { CitationDrawer } from "@/components/citations/citation-drawer";
import { PdfViewerModal } from "@/components/pdf/pdf-viewer-modal";
import { AuthModal } from "@/components/auth/auth-modal";
import { UploadModal } from "@/components/documents/upload-modal";
import { getSupabase } from "@/lib/supabase";
import { useFDISStore } from "@/store/useFDISStore";
export function WorkspaceShell({ children }: { children: React.ReactNode }) {
  const queryClient = useQueryClient();
  const { setCurrentUser, currentUser } = useFDISStore();
  const pathname = usePathname();
  useEffect(() => {
    let active = true;
    let authEventSeen = false;
    const apply = (
      user:
        | { id: string; email?: string; user_metadata?: Record<string, any> }
        | null
        | undefined,
    ) => {
      if (!active) return;
      setCurrentUser(
        user
          ? {
              id: user.id,
              email: user.email,
              name: user.user_metadata?.full_name || user.email,
              avatarUrl: user.user_metadata?.avatar_url,
            }
          : null,
      );
    };
    const supabase = getSupabase();
    if (!supabase) return;
    const { data: sub } = supabase.auth.onAuthStateChange((_event, session) => {
      authEventSeen = true;
      apply(session?.user);
      queryClient.removeQueries({ queryKey: ["documents"] });
    });
    supabase.auth.getSession().then(({ data }) => {
      if (!authEventSeen) apply(data.session?.user);
    });
    return () => {
      active = false;
      sub.subscription.unsubscribe();
    };
  }, [setCurrentUser, queryClient]);
  useEffect(() => {
    useFDISStore.getState().setActiveCitation(null);
    useFDISStore.getState().closePdfViewer();
    useFDISStore.getState().setUploadOpen(false);
  }, [pathname]);
  return (
    <div className="v8-green flex h-dvh min-w-0 flex-col overflow-hidden bg-[#EAF1E4] p-2 sm:p-4">
      <div className="flex min-h-0 flex-1 flex-col overflow-hidden rounded-[24px] bg-[#F9FBF8] shadow-sm">
        <TopNav />
        <div
          key={currentUser?.id || "guest"}
          className="flex min-h-0 min-w-0 flex-1 overflow-hidden"
        >
          {children}
        </div>
      </div>
      <CitationDrawer />
      <PdfViewerModal />
      <AuthModal />
      <UploadModal
        key={currentUser?.id || "guest"}
        onUploaded={() => {
          queryClient.invalidateQueries({ queryKey: ["documents"] });
        }}
      />
    </div>
  );
}
