"use client";

import { usePrinterStatus } from "@/hooks/use-printer-status";

export function PrinterStatus() {
  const { online, loading, printers, selectedQueue, error, refresh } = usePrinterStatus();

  return (
    <div className="flex items-center justify-between rounded-lg border border-zinc-200 bg-white px-4 py-3 text-sm dark:border-zinc-800 dark:bg-zinc-900">
      <div className="flex items-center gap-2">
        <span
          className={`h-2.5 w-2.5 rounded-full ${
            loading
              ? "bg-zinc-300 animate-pulse"
              : online
                ? "bg-green-500"
                : "bg-red-500"
          }`}
        />
        <span className="font-medium">
          {loading ? "检测中…" : online ? "后端服务已连接" : "后端服务未连接"}
        </span>
        {online && printers.length > 0 && (
          <span className="text-zinc-500">
            · 打印机：
            {printers.map((p) => {
              const selected = p.name === selectedQueue ? "✓ " : "";
              return `${selected}${p.name}（${p.status}）`;
            }).join("、")}
          </span>
        )}
        {online && printers.length === 0 && (
          <span className="text-amber-600">· 未检测到可用打印机</span>
        )}
        {!loading && !online && error && (
          <span className="text-red-500">· {error}</span>
        )}
      </div>
      <button
        type="button"
        onClick={refresh}
        className="text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100"
      >
        刷新
      </button>
    </div>
  );
}
