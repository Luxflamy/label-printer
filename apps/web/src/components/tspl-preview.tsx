"use client";

interface TsplPreviewProps {
  tspl: string | null;
  loading?: boolean;
  error?: string | null;
}

export function TsplPreview({ tspl, loading, error }: TsplPreviewProps) {
  return (
    <div className="rounded-lg border border-zinc-200 bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-950">
      <div className="border-b border-zinc-200 px-3 py-2 text-xs font-medium text-zinc-500 dark:border-zinc-800">
        TSPL 预览
      </div>
      <div className="max-h-64 overflow-auto p-3">
        {loading && <p className="text-sm text-zinc-400">正在生成预览…</p>}
        {!loading && error && <p className="text-sm text-red-500">{error}</p>}
        {!loading && !error && !tspl && (
          <p className="text-sm text-zinc-400">点击&ldquo;预览&rdquo;查看将要发送的 TSPL 指令</p>
        )}
        {!loading && !error && tspl && (
          <pre className="whitespace-pre-wrap break-all font-mono text-xs text-zinc-700 dark:text-zinc-300">
            {tspl}
          </pre>
        )}
      </div>
    </div>
  );
}
