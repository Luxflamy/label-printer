"use client";

import type { PrinterInfo } from "@/types/api";

const STATUS_LABEL: Record<string, string> = {
  idle: "闲置",
  printing: "打印中",
  disabled: "已停用",
  unknown: "未知",
};

const STATUS_DOT: Record<string, string> = {
  idle: "bg-green-500",
  printing: "bg-blue-500 animate-pulse",
  disabled: "bg-zinc-400",
  unknown: "bg-amber-500",
};

function formatAgo(date: Date | null): string {
  if (!date) return "";
  const sec = Math.max(0, Math.floor((Date.now() - date.getTime()) / 1000));
  if (sec < 5) return "刚刚更新";
  return `${sec} 秒前更新`;
}

interface PrinterPickerProps {
  printers: PrinterInfo[];
  selectedQueue: string | null;
  loading?: boolean;
  selecting?: boolean;
  error?: string | null;
  lastUpdated?: Date | null;
  onSelect: (queue: string) => void;
  onRefresh: () => void;
}

/** 打印机选择 — 纵向列表 + 状态圆点，嵌入打印队列面板。 */
export function PrinterPicker({
  printers,
  selectedQueue,
  loading,
  selecting,
  error,
  lastUpdated,
  onSelect,
  onRefresh,
}: PrinterPickerProps) {
  return (
    <div className="flex flex-col gap-2 border-b border-zinc-100 pb-3 dark:border-zinc-800">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-zinc-500">选择打印机</span>
        <div className="flex items-center gap-2">
          {lastUpdated && (
            <span className="text-[10px] text-zinc-400">{formatAgo(lastUpdated)}</span>
          )}
          <button
            type="button"
            onClick={onRefresh}
            disabled={loading || selecting}
            className="text-[10px] text-zinc-500 hover:text-zinc-800 disabled:opacity-40 dark:hover:text-zinc-200"
          >
            刷新
          </button>
        </div>
      </div>

      {loading && printers.length === 0 && (
        <p className="text-xs text-zinc-400">正在检测打印机…</p>
      )}

      {!loading && printers.length === 0 && (
        <p className="text-xs text-amber-600 dark:text-amber-400">
          未检测到打印机，请先在「系统设置 → 打印机与扫描仪」中添加
        </p>
      )}

      {error && <p className="text-xs text-red-500">{error}</p>}

      <div className="flex flex-col gap-1">
        {printers.map((printer) => {
          const isActive = printer.name === selectedQueue;
          const statusKey = printer.status in STATUS_LABEL ? printer.status : "unknown";
          return (
            <button
              key={printer.name}
              type="button"
              disabled={selecting}
              onClick={() => onSelect(printer.name)}
              className={`flex items-center gap-2 rounded-md border px-2 py-1 text-left transition-colors disabled:opacity-50 ${
                isActive
                  ? "border-zinc-900 bg-zinc-900 text-white dark:border-zinc-100 dark:bg-zinc-100 dark:text-zinc-900"
                  : "border-zinc-200 bg-white text-zinc-700 hover:border-zinc-400 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-300 dark:hover:border-zinc-500"
              }`}
            >
              <span
                className={`h-2 w-2 shrink-0 rounded-full ${STATUS_DOT[statusKey]}`}
                aria-hidden
              />
              <span className="min-w-0 flex-1 truncate text-xs font-medium">
                {printer.name}
              </span>
              <span
                className={`shrink-0 text-[10px] ${
                  isActive ? "text-zinc-300 dark:text-zinc-600" : "text-zinc-400"
                }`}
              >
                {STATUS_LABEL[statusKey]}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
