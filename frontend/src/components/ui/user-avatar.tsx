/**
 * @source DiceBear API (Zero-Auth)
 * @style notionists — Minimalist illustration (Notion/Linear aesthetic)
 * @docs https://api.dicebear.com/7.x/notionists/svg
 */
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

interface UserAvatarProps {
  name: string;
  email?: string;
  style?: "notionists" | "bottts" | "identicon" | "initials";
  size?: "sm" | "md" | "lg";
}

const sizeMap = {
  sm: "size-7",
  md: "size-9",
  lg: "size-11",
} as const;

export function UserAvatar({
  name,
  email,
  style = "notionists",
  size = "md",
}: UserAvatarProps) {
  const seed = encodeURIComponent(email || name);
  const avatarUrl = `https://api.dicebear.com/7.x/${style}/svg?seed=${seed}&backgroundColor=b6e3f4,c0aede,d1d4f9&radius=50`;
  const initials = name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);

  return (
    <Avatar className={`${sizeMap[size]} border border-border/60`}>
      <AvatarImage src={avatarUrl} alt={name} />
      <AvatarFallback className="bg-muted text-muted-foreground text-xs font-medium">
        {initials}
      </AvatarFallback>
    </Avatar>
  );
}
