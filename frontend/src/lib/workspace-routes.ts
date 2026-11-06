import type { DashboardTab } from "@/store/useFDISStore";
export const TAB_PATHS: Record<DashboardTab, string> = {
  overview: "/workspace",
  chat: "/qa",
  documents: "/documents",
  statements: "/statements",
  comparison: "/comparison",
  insights: "/insights",
};
export function tabForPath(path: string): DashboardTab | null {
  return (
    (Object.keys(TAB_PATHS) as DashboardTab[]).find(
      (t) => TAB_PATHS[t] === path,
    ) ?? null
  );
}
export function safeReturnPath(path: string): string {
  try {
    const url = new URL(path, "https://fdis.invalid");
    if (url.origin !== "https://fdis.invalid" || !tabForPath(url.pathname))
      return "/workspace";
    const id = url.searchParams.get("document");
    return (
      url.pathname +
      (url.pathname === "/qa" && id && /^[0-9a-f-]{36}$/i.test(id)
        ? "?document=" + encodeURIComponent(id)
        : "")
    );
  } catch {
    return "/workspace";
  }
}
