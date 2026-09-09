"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { apiClient } from "@/lib/api-client";
import type { PrinterInfo } from "@/types/api";

const POLL_ACTIVE_MS = 500;
const POLL_HIDDEN_MS = 60_000;

function pollIntervalMs(): number {
  if (typeof document === "undefined") return POLL_ACTIVE_MS;
  return document.visibilityState === "visible" ? POLL_ACTIVE_MS : POLL_HIDDEN_MS;
}

interface PrintersState {
  printers: PrinterInfo[];
  selectedQueue: string | null;
  loading: boolean;
  selecting: boolean;
  error: string | null;
  lastUpdated: Date | null;
}

interface UsePrintersOptions {
  /** 页面进入后若该队列在线，则自动选中一次（不反复覆盖用户手动切换） */
  preferredQueue?: string;
}

/** 页面可见时 0.5s 轮询，隐藏时 60s；选中写回 printer.yaml。 */
export function usePrinters(options: UsePrintersOptions = {}) {
  const { preferredQueue } = options;
  const [state, setState] = useState<PrintersState>({
    printers: [],
    selectedQueue: null,
    loading: true,
    selecting: false,
    error: null,
    lastUpdated: null,
  });
  const mounted = useRef(true);
  const preferredApplied = useRef(false);

  const refresh = useCallback(async (silent = false) => {
    if (!silent) {
      setState((prev) => ({ ...prev, loading: true }));
    }
    try {
      await apiClient.health();
      const data = await apiClient.listPrinters();
      if (!mounted.current) return;
      setState({
        printers: data.printers,
        selectedQueue: data.selected_queue,
        loading: false,
        selecting: false,
        error: null,
        lastUpdated: new Date(),
      });
    } catch (err) {
      if (!mounted.current) return;
      setState((prev) => ({
        ...prev,
        loading: false,
        selecting: false,
        error: err instanceof Error ? err.message : "无法连接后端服务",
      }));
    }
  }, []);

  const selectPrinter = useCallback(async (queue: string) => {
    setState((prev) => ({ ...prev, selecting: true, error: null }));
    try {
      const data = await apiClient.selectPrinter(queue);
      if (!mounted.current) return;
      setState({
        printers: data.printers,
        selectedQueue: data.selected_queue,
        loading: false,
        selecting: false,
        error: null,
        lastUpdated: new Date(),
      });
    } catch (err) {
      if (!mounted.current) return;
      setState((prev) => ({
        ...prev,
        selecting: false,
        error: err instanceof Error ? err.message : "选择打印机失败",
      }));
    }
  }, []);

  useEffect(() => {
    preferredApplied.current = false;
  }, [preferredQueue]);

  useEffect(() => {
    if (!preferredQueue || preferredApplied.current) return;
    if (state.loading || state.selecting) return;
    if (state.printers.length === 0) return;
    const exists = state.printers.some((p) => p.name === preferredQueue);
    if (!exists) return;
    preferredApplied.current = true;
    if (state.selectedQueue !== preferredQueue) {
      void selectPrinter(preferredQueue);
    }
  }, [
    preferredQueue,
    state.loading,
    state.selecting,
    state.printers,
    state.selectedQueue,
    selectPrinter,
  ]);

  useEffect(() => {
    mounted.current = true;
    let timer: ReturnType<typeof setInterval> | undefined;

    const startPolling = () => {
      if (timer !== undefined) clearInterval(timer);
      timer = setInterval(() => refresh(true), pollIntervalMs());
    };

    const handleVisibilityChange = () => {
      if (document.visibilityState === "visible") {
        refresh(true);
      }
      startPolling();
    };

    refresh();
    startPolling();
    document.addEventListener("visibilitychange", handleVisibilityChange);

    return () => {
      mounted.current = false;
      if (timer !== undefined) clearInterval(timer);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, [refresh]);

  return { ...state, refresh: () => refresh(false), selectPrinter };
}
