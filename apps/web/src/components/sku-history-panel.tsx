"use client";

import { useState } from "react";
import type { SkuRecord } from "@/types/api";

function formatTime(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return date.toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

interface SkuHistoryPanelProps {
  items: SkuRecord[];
  loading?: boolean;
  error?: string | null;
  onSearch: (keyword: string) => void;
  onPick: (sku: string) => void;
  onRemove: (sku: string) => void;
}

/** 已打印 SKU 查询面板 — 搜索、回填到输入框、删除误记录。 */
export function SkuHistoryPanel({
  items,
  loading,
  error,
  onSearch,
  onPick,
  onRemove,
}: SkuHistoryPanelProps) {
  const [keyword, setKeyword] = useState("");

  return (
    <div className="flex h-full flex-col gap-3">
      <div className="flex flex-col gap-1">
        <label htmlFor="sku-search" className="text-xs font-medium text-zinc-500">
          查询已打印过的 SKU
        </label>
        <input
          id="sku-search"
          type="search"
          value={keyword}
          placeholder="输入关键词过滤…"
          autoComplete="off"
          onChange={(e) => {
            setKeyword(e.target.value);
            onSearch(e.target.value);
          }}
          className="rounded-md border border-zinc-300 px-3 py-1.5 text-sm outline-none focus:border-zinc-900 dark:border-zinc-700 dark:bg-zinc-900 dark:focus:border-zinc-100"
        />
      </div>

      {error && <p className="text-xs text-red-500">{error}</p>}

      {loading && items.length === 0 && (
        <p className="text-xs text-zinc-400">正在加载历史…</p>
      )}

      {!loading && items.length === 0 && (
        <p className="text-xs text-zinc-400">
          {keyword ? "没有匹配的 SKU" : "还没有打印记录，打印后会自动出现在这里"}
        </p>
      )}

      <ul className="flex min-h-0 flex-1 flex-col gap-1 overflow-y-auto">
        {items.map((record) => (
          <li
            key={record.sku}
            className="group flex items-center gap-2 rounded-md border border-zinc-200 px-2.5 py-1.5 dark:border-zinc-800"
          >
            <button
              type="button"
              onClick={() => onPick(record.sku)}
              title="填入输入框"
              className="min-w-0 flex-1 truncate text-left font-mono text-xs font-medium text-zinc-800 hover:underline dark:text-zinc-100"
            >
              {record.sku}
            </button>
            <span className="shrink-0 text-[10px] text-zinc-400">
              {record.print_count} 次 · {formatTime(record.last_printed_at)}
            </span>
            <button
              type="button"
              onClick={() => {
                if (window.confirm(`确定从历史中删除「${record.sku}」？`)) {
                  onRemove(record.sku);
                }
              }}
              title="删除该记录"
              className="shrink-0 text-xs text-zinc-300 opacity-0 transition-opacity hover:text-red-500 group-hover:opacity-100 dark:text-zinc-600"
            >
              ×
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
