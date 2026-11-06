import { cn } from "@/lib/utils";

export type OrbKind = "green" | "purple" | "warm";

/** Soft radial-gradient orb used across the v8 design (CSS-only, editable). */
export function Orb({
  kind,
  className,
}: {
  kind: OrbKind;
  className?: string;
}) {
  return (
    <div
      aria-hidden
      className={cn(
        "rounded-full shrink-0",
        kind === "green" && "orb-green",
        kind === "purple" && "orb-purple",
        kind === "warm" && "orb-warm",
        className,
      )}
    />
  );
}
