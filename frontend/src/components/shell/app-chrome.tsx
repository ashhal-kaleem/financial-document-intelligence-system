"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useFDISStore, type DashboardTab } from "@/store/useFDISStore";
import { TAB_PATHS } from "@/lib/workspace-routes";
import { cn } from "@/lib/utils";
export const NAV_ITEMS: { id: DashboardTab; label: string }[] = [
  { id: "overview", label: "Overview" },
  { id: "documents", label: "Documents" },
  { id: "chat", label: "Q&A" },
];
export function initialsOf(name?: string | null) {
  return (
    name
      ?.trim()
      .split(/\s+/)
      .slice(0, 2)
      .map((x) => x[0])
      .join("") || "G"
  );
}
export function AvatarCircle({
  name,
  className,
}: {
  name?: string | null;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex shrink-0 items-center justify-center rounded-full bg-[#EAF1E4] text-[#174A37]",
        className,
      )}
    >
      {initialsOf(name)}
    </span>
  );
}
export function ProfileChip() {
  const { currentUser, setAuthModalOpen } = useFDISStore();
  return (
    <button
      onClick={() => setAuthModalOpen(true)}
      className="flex min-h-11 max-w-[170px] items-center gap-2 rounded-full border border-[#DBE5DA] bg-white px-3 text-xs"
      aria-label={currentUser ? "Account and sign out" : "Sign in"}
    >
      <AvatarCircle name={currentUser?.name} className="size-7" />
      <span className="truncate">
        {currentUser ? currentUser.name || "Account" : "Sign in"}
      </span>
    </button>
  );
}
export function LogoMark() {
  return (
    <Link href="/workspace" className="text-base font-semibold text-[#0C3B2E]">
      FDIS
    </Link>
  );
}
export function TopNav() {
  const path = usePathname();
  return (
    <header className="shrink-0 border-b border-[#E2E9DF] px-3 py-3 sm:px-6">
      <div className="flex items-center justify-between gap-3">
        <LogoMark />
        <ProfileChip />
      </div>
      <nav aria-label="Workspace" className="mt-3 flex gap-1">
        {NAV_ITEMS.map((item) => (
          <Link
            key={item.id}
            href={TAB_PATHS[item.id]}
            aria-current={path === TAB_PATHS[item.id] ? "page" : undefined}
            className={cn(
              "min-h-11 rounded-full px-4 py-3 text-xs sm:text-sm",
              path === TAB_PATHS[item.id]
                ? "bg-[#CDEFA6] font-semibold text-[#123D2B]"
                : "text-[#506150] hover:bg-[#EDF3E8]",
            )}
          >
            {item.label}
          </Link>
        ))}
      </nav>
    </header>
  );
}
export function ChatSidebar({
  history,
  onPick,
}: {
  history: string[];
  onPick: (q: string) => void;
}) {
  const user = useFDISStore((s) => s.currentUser);
  if (!user) return null;
  return (
    <aside className="hidden w-52 shrink-0 flex-col gap-3 border-r border-[#E7E2ED] bg-[#F5F2FA] p-4 lg:flex">
      <p className="text-xs leading-5 text-[#6B6278]">
        Questions from this conversation. Select one to reuse it in the draft.
      </p>
      <h2 className="mt-3 text-xs font-semibold">Recent questions</h2>
      <div className="min-h-0 overflow-y-auto">
        {history.length ? (
          history.slice(0, 8).map((q, i) => (
            <button
              key={i}
              onClick={() => onPick(q)}
              className="mb-1 block min-h-11 w-full truncate rounded-lg p-2 text-left text-xs hover:bg-[#E9E1F2]"
              title={q}
            >
              {q}
            </button>
          ))
        ) : (
          <p className="text-xs text-[#6B6278]">No questions yet.</p>
        )}
      </div>
    </aside>
  );
}
