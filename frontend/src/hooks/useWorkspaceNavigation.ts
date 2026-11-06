"use client";
import { usePathname, useRouter } from "next/navigation";
import { TAB_PATHS, tabForPath } from "@/lib/workspace-routes";
import { useFDISStore, type DashboardTab } from "@/store/useFDISStore";
export function useWorkspaceNavigation() {
  const path = usePathname();
  const router = useRouter();
  return {
    activeTab: tabForPath(path),
    setActiveTab: (tab: DashboardTab) => {
      const doc = useFDISStore.getState().selectedDocument;
      const target =
        TAB_PATHS[tab] +
        (tab === "chat" && doc
          ? `?document=${encodeURIComponent(doc.id)}`
          : "");
      if (target !== path + window.location.search) router.push(target);
    },
  };
}
