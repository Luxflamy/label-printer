"use client";

interface StatusBannerProps {
  kind: "success" | "warning" | "error";
  message: string;
}

const KIND_STYLES: Record<StatusBannerProps["kind"], string> = {
  success:
    "border-green-200 bg-green-50 text-green-700 dark:border-green-900 dark:bg-green-950 dark:text-green-300",
  warning:
    "border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-800 dark:bg-amber-900/20 dark:text-amber-300",
  error:
    "border-red-200 bg-red-50 text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300",
};

export function StatusBanner({ kind, message }: StatusBannerProps) {
  return (
    <div className={`rounded-lg border px-4 py-3 text-sm ${KIND_STYLES[kind]}`}>
      {message}
    </div>
  );
}
