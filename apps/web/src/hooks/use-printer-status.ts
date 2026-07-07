"use client";

import { useCallback, useEffect, useState } from "react";
import { apiClient } from "@/lib/api-client";
import type { PrinterInfo } from "@/types/api";

interface PrinterStatusState {
  online: boolean;
  loading: boolean;
  printers: PrinterInfo[];
  error: string | null;
}

/** 探测本地 API 是否在线、以及可用的 CUPS 打印机列表。 */
export function usePrinterStatus() {
  const [state, setState] = useState<PrinterStatusState>({
    online: false,
    loading: true,
    printers: [],
    error: null,
  });

  const refresh = useCallback(async () => {
    setState((prev) => ({ ...prev, loading: true }));
    try {
      await apiClient.health();
      const printers = await apiClient.listPrinters();
      setState({ online: true, loading: false, printers, error: null });
    } catch (err) {
      setState({
        online: false,
        loading: false,
        printers: [],
        error: err instanceof Error ? err.message : "无法连接后端服务",
      });
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { ...state, refresh };
}
