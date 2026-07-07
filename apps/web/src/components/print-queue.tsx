"use client";

import { useRef, useState } from "react";
import { QueueItem } from "./queue-item";
import type { ProductItem, QueueEntry } from "@/types/api";

interface Props {
  queue: QueueEntry[];
  onAdd: (product: ProductItem) => void;
  onCopiesChange: (productId: string, copies: number) => void;
  onRemove: (productId: string) => void;
  onReorder: (from: number, to: number) => void;
  onClear: () => void;
}

/** 右侧打印队列面板：拖放接收（来自商品库）+ 队列内拖拽排序。 */
export function PrintQueue({ queue, onAdd, onCopiesChange, onRemove, onReorder, onClear }: Props) {
  const [isDragOver, setIsDragOver] = useState(false);
  const dragFromIdx = useRef<number | null>(null);
  const dragToIdx = useRef<number | null>(null);

  /* ---- 外部商品拖入（DataTransfer） ---- */
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };
  const handleDragLeave = () => setIsDragOver(false);
  const handleExternalDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    const raw = e.dataTransfer.getData("application/json");
    if (!raw) return;
    try {
      const product: ProductItem = JSON.parse(raw);
      onAdd(product);
    } catch {}
  };

  /* ---- 队列内拖拽排序 ---- */
  const handleItemDragStart = (index: number) => {
    dragFromIdx.current = index;
  };
  const handleItemDragOver = (index: number) => {
    dragToIdx.current = index;
  };
  const handleItemDrop = () => {
    if (dragFromIdx.current !== null && dragToIdx.current !== null) {
      onReorder(dragFromIdx.current, dragToIdx.current);
    }
    dragFromIdx.current = null;
    dragToIdx.current = null;
  };

  return (
    <div className="flex h-full flex-col gap-3">
      <div className="flex items-center justify-between">
        <p className="text-xs text-zinc-400">
          队列共 {queue.length} 种 · 合计{" "}
          {queue.reduce((s, e) => s + e.copies, 0)} 张
        </p>
        {queue.length > 0 && (
          <button
            type="button"
            onClick={onClear}
            className="text-xs text-zinc-400 hover:text-red-500"
          >
            清空队列
          </button>
        )}
      </div>

      {/* 拖放接收区 */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleExternalDrop}
        className={`flex-1 overflow-y-auto rounded-xl border-2 border-dashed p-2 transition-colors ${
          isDragOver
            ? "border-blue-400 bg-blue-50 dark:border-blue-500 dark:bg-blue-900/10"
            : "border-zinc-200 dark:border-zinc-700"
        }`}
      >
        {queue.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center gap-2 text-center">
            <span className="text-3xl text-zinc-200 dark:text-zinc-700">⬇</span>
            <p className="text-sm text-zinc-400">将左侧商品拖到这里</p>
            <p className="text-xs text-zinc-300 dark:text-zinc-600">或点击商品卡片快速添加</p>
          </div>
        ) : (
          <div className="flex flex-col gap-2">
            {queue.map((entry, i) => (
              <QueueItem
                key={entry.product.id}
                entry={entry}
                index={i}
                onCopiesChange={onCopiesChange}
                onRemove={onRemove}
                onDragStart={handleItemDragStart}
                onDragOver={handleItemDragOver}
                onDrop={handleItemDrop}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
