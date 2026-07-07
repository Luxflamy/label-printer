"use client";

import { useState } from "react";
import { ApiError, apiClient } from "@/lib/api-client";
import type { BatchPrintData, QueueEntry } from "@/types/api";

interface BatchState {
  loading: boolean;
  result: BatchPrintData | null;
  error: string | null;
}

export function useBatchPrint() {
  const [state, setState] = useState<BatchState>({
    loading: false,
    result: null,
    error: null,
  });

  const print = async (templateId: string, storeId: string, queue: QueueEntry[]) => {
    if (queue.length === 0) return;
    setState({ loading: true, result: null, error: null });
    try {
      const result = await apiClient.batchPrint({
        template: templateId,
        store: storeId,
        items: queue.map((e) => ({ product_id: e.product.id, copies: e.copies })),
      });
      setState({ loading: false, result, error: null });
    } catch (err) {
      setState({
        loading: false,
        result: null,
        error: err instanceof ApiError ? err.message : "批量打印失败",
      });
    }
  };

  const reset = () => setState({ loading: false, result: null, error: null });

  return { ...state, print, reset };
}
