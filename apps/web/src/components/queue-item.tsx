"use client";

import type { QueueEntry } from "@/types/api";

interface Props {
  entry: QueueEntry;
  index: number;
  onCopiesChange: (productId: string, copies: number) => void;
  onRemove: (productId: string) => void;
  onDragStart: (index: number) => void;
  onDragOver: (index: number) => void;
  onDrop: () => void;
}

/** 打印队列中的单行条目：拖拽排序 + 份数输入 + 删除。 */
export function QueueItem({ entry, index, onCopiesChange, onRemove, onDragStart, onDragOver, onDrop }: Props) {
  return (
    <div
      draggable
      onDragStart={() => onDragStart(index)}
      onDragOver={(e) => { e.preventDefault(); onDragOver(index); }}
      onDrop={onDrop}
      className="flex items-center gap-3 rounded-lg border border-zinc-200 bg-white px-3 py-2 shadow-sm dark:border-zinc-700 dark:bg-zinc-900"
    >
      {/* 拖拽手柄 */}
      <span className="cursor-grab text-zinc-300 select-none active:cursor-grabbing dark:text-zinc-600">
        ⠿
      </span>

      {/* 商品信息 */}
      <div className="flex min-w-0 flex-1 flex-col gap-0.5">
        <span className="truncate font-mono text-xs font-semibold text-zinc-800 dark:text-zinc-100">
          {entry.product.sku}
        </span>
        <span className="truncate text-xs text-zinc-400">{entry.product.fnsku}</span>
      </div>

      {/* 份数输入 */}
      <label className="flex items-center gap-1 text-xs text-zinc-500">
        份数
        <input
          type="number"
          min={1}
          max={999}
          value={entry.copies}
          onChange={(e) => onCopiesChange(entry.product.id, Number(e.target.value))}
          className="w-16 rounded border border-zinc-200 bg-white px-2 py-1 text-center text-sm tabular-nums focus:border-blue-400 focus:outline-none dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100"
        />
      </label>

      {/* 删除 */}
      <button
        type="button"
        onClick={() => onRemove(entry.product.id)}
        title="从队列移除"
        className="rounded p-1 text-zinc-400 hover:bg-red-50 hover:text-red-500 dark:hover:bg-red-900/20"
      >
        ✕
      </button>
    </div>
  );
}
