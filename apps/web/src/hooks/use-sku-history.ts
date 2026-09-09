"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError, apiClient } from "@/lib/api-client";
import type { SkuRecord } from "@/types/api";

const DEBOUNCE_MS = 250;

/**
 * 已打印 SKU 历史查询。
 *
 * 搜索走服务端（防抖），保证历史条目变多后仍能查到全部记录；
 * 页面可创建多个实例分别服务「输入补全」与「查询面板」，互不干扰。
 */
export function useSkuHistory(limit = 20) {
  const [items, setItems] = useState<SkuRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const keywordRef = useRef("");
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const fetchHistory = useCallback(
    async (keyword: string) => {
      setLoading(true);
      try {
        const data = await apiClient.listSkuHistory(keyword, limit);
        setItems(data.items);
        setError(null);
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "查询 SKU 历史失败");
      } finally {
        setLoading(false);
      }
    },
    [limit]
  );

  useEffect(() => {
    fetchHistory("");
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [fetchHistory]);

  const search = useCallback(
    (keyword: string) => {
      keywordRef.current = keyword;
      if (timerRef.current) clearTimeout(timerRef.current);
      timerRef.current = setTimeout(() => fetchHistory(keyword), DEBOUNCE_MS);
    },
    [fetchHistory]
  );

  const refresh = useCallback(
    () => fetchHistory(keywordRef.current),
    [fetchHistory]
  );

  const remove = useCallback(
    async (sku: string) => {
      try {
        await apiClient.deleteSkuHistory(sku);
        await fetchHistory(keywordRef.current);
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "删除历史记录失败");
      }
    },
    [fetchHistory]
  );

  return { items, loading, error, search, refresh, remove };
}
