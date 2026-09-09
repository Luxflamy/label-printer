"use client";

import { useCallback, useState } from "react";
import { ApiError, apiClient } from "@/lib/api-client";
import type { SkuLabelPrintData } from "@/types/api";

/** 自定义 SKU 小标签打印动作与状态。 */
export function useSkuPrint(printer: string | null) {
  const [printing, setPrinting] = useState(false);
  const [result, setResult] = useState<SkuLabelPrintData | null>(null);
  const [error, setError] = useState<string | null>(null);

  const print = useCallback(
    async (sku: string, copies: number): Promise<SkuLabelPrintData | null> => {
      const normalized = sku.trim();
      if (!normalized) {
        setError("请先输入 SKU");
        return null;
      }
      if (!printer) {
        setError("请先选择打印机");
        return null;
      }

      setPrinting(true);
      setResult(null);
      setError(null);
      try {
        const data = await apiClient.printSkuLabel({
          sku: normalized,
          copies,
          printer,
        });
        setResult(data);
        return data;
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "打印失败");
        return null;
      } finally {
        setPrinting(false);
      }
    },
    [printer]
  );

  const reset = useCallback(() => {
    setResult(null);
    setError(null);
  }, []);

  return { printing, result, error, print, reset };
}
