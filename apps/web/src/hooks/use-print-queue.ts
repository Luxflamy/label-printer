"use client";

import { useCallback, useState } from "react";
import type { ProductItem, QueueEntry } from "@/types/api";

/** 管理打印队列的增删改查（纯本地状态）。 */
export function usePrintQueue() {
  const [queue, setQueue] = useState<QueueEntry[]>([]);

  /** 添加商品到队列；若已存在则份数 +1。 */
  const addToQueue = useCallback((product: ProductItem) => {
    setQueue((prev) => {
      const idx = prev.findIndex((e) => e.product.id === product.id);
      if (idx >= 0) {
        const next = [...prev];
        next[idx] = { ...next[idx], copies: next[idx].copies + 1 };
        return next;
      }
      return [...prev, { product, copies: 1 }];
    });
  }, []);

  /** 更新某条目的份数。 */
  const setCopies = useCallback((productId: string, copies: number) => {
    setQueue((prev) =>
      prev.map((e) => (e.product.id === productId ? { ...e, copies: Math.max(1, copies) } : e))
    );
  }, []);

  /** 从队列移除。 */
  const removeFromQueue = useCallback((productId: string) => {
    setQueue((prev) => prev.filter((e) => e.product.id !== productId));
  }, []);

  const clearQueue = useCallback(() => setQueue([]), []);

  /** 队列内拖拽排序：把 from 位置的条目移到 to 位置。 */
  const reorderQueue = useCallback((from: number, to: number) => {
    if (from === to) return;
    setQueue((prev) => {
      const next = [...prev];
      const [moved] = next.splice(from, 1);
      next.splice(to, 0, moved);
      return next;
    });
  }, []);

  return { queue, addToQueue, setCopies, removeFromQueue, clearQueue, reorderQueue };
}
