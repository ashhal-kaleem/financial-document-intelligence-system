/**
 * @source LottieFiles / DotLottie React
 * @assets /public/animations/success.json, loading-pulse.json, empty-docs.json
 * @docs https://lottiefiles.com
 */
"use client";

import { DotLottieReact } from "@lottiefiles/dotlottie-react";

interface LottiePlayerProps {
  src: string;
  loop?: boolean;
  autoplay?: boolean;
  className?: string;
}

export function LottiePlayer({
  src,
  loop = true,
  autoplay = true,
  className = "size-24",
}: LottiePlayerProps) {
  return (
    <DotLottieReact
      src={src}
      loop={loop}
      autoplay={autoplay}
      className={className}
    />
  );
}

/** Pre-configured animation variants */
export function SuccessAnimation({ className }: { className?: string }) {
  return (
    <LottiePlayer
      src="/animations/success.json"
      loop={false}
      className={className || "size-20"}
    />
  );
}

export function LoadingPulseAnimation({ className }: { className?: string }) {
  return (
    <LottiePlayer
      src="/animations/loading-pulse.json"
      loop={true}
      className={className || "size-16"}
    />
  );
}

export function EmptyDocsAnimation({ className }: { className?: string }) {
  return (
    <LottiePlayer
      src="/animations/empty-docs.json"
      loop={true}
      className={className || "size-32"}
    />
  );
}
