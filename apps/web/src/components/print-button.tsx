"use client";

interface PrintButtonProps {
  loading: boolean;
  disabled?: boolean;
  onClick: () => void;
}

export function PrintButton({ loading, disabled, onClick }: PrintButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled || loading}
      className="rounded-full bg-zinc-900 px-6 py-2.5 font-medium text-white transition-colors hover:bg-zinc-700 disabled:cursor-not-allowed disabled:bg-zinc-300 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300 dark:disabled:bg-zinc-700"
    >
      {loading ? "打印中…" : "打印"}
    </button>
  );
}
