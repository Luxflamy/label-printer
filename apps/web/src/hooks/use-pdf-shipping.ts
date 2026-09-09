"use client";

import { useCallback, useEffect, useState } from "react";
import { ApiError, apiClient } from "@/lib/api-client";
import type { FitMode, ShippingLabelPreviewData } from "@/types/api";

/** 与后端 DEFAULT_PRINT_SCALE 一致 */
export const DEFAULT_PRINT_SCALE = 0.94;

interface PdfShippingState {
  file: File | null;
  preview: ShippingLabelPreviewData | null;
  page: number;
  copies: number;
  rotation: number;
  fitMode: FitMode;
  scale: number;
  printAllPages: boolean;
  previewing: boolean;
  printing: boolean;
  error: string | null;
  printSuccess: string | null;
}

export function usePdfShipping(printer: string | null) {
  const [state, setState] = useState<PdfShippingState>({
    file: null,
    preview: null,
    page: 0,
    copies: 1,
    rotation: 0,
    fitMode: "contain",
    scale: DEFAULT_PRINT_SCALE,
    printAllPages: false,
    previewing: false,
    printing: false,
    error: null,
    printSuccess: null,
  });

  const loadPreview = useCallback(
    async (
      file: File,
      page: number,
      fitMode: FitMode,
      rotation: number,
      scale: number,
      activePrinter: string | null
    ) => {
      setState((prev) => ({ ...prev, previewing: true, error: null, printSuccess: null }));
      try {
        const preview = await apiClient.previewShippingLabel(file, {
          page,
          fit_mode: fitMode,
          rotation,
          scale,
          printer: activePrinter,
        });
        setState((prev) => ({
          ...prev,
          preview,
          previewing: false,
          page: preview.page,
          // 仅首次解析该 PDF 时自动勾选多页；后续预览刷新保留用户选择
          printAllPages:
            prev.preview == null ? preview.page_count > 1 : prev.printAllPages,
        }));
      } catch (err) {
        setState((prev) => ({
          ...prev,
          previewing: false,
          error: err instanceof ApiError ? err.message : "PDF 预览失败",
        }));
      }
    },
    []
  );

  const setFile = useCallback(
    (file: File) => {
      setState((prev) => ({
        ...prev,
        file,
        page: 0,
        preview: null,
        error: null,
        printSuccess: null,
      }));
      loadPreview(file, 0, "contain", 0, DEFAULT_PRINT_SCALE, printer);
    },
    [loadPreview, printer]
  );

  useEffect(() => {
    if (!state.file) return;
    loadPreview(
      state.file,
      state.page,
      state.fitMode,
      state.rotation,
      state.scale,
      printer
    );
    // 切换打印机时按新 DPI 重新预览
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [printer]);

  const clearFile = useCallback(() => {
    setState((prev) => ({
      ...prev,
      file: null,
      preview: null,
      page: 0,
      error: null,
      printSuccess: null,
    }));
  }, []);

  const setPage = useCallback(
    (page: number) => {
      setState((prev) => {
        if (!prev.file) return prev;
        loadPreview(prev.file, page, prev.fitMode, prev.rotation, prev.scale, printer);
        return { ...prev, page };
      });
    },
    [loadPreview, printer]
  );

  const setCopies = useCallback((copies: number) => {
    setState((prev) => ({ ...prev, copies: Math.max(1, Math.min(99, copies)) }));
  }, []);

  const setRotation = useCallback(
    (rotation: number) => {
      setState((prev) => {
        if (!prev.file) return { ...prev, rotation };
        loadPreview(prev.file, prev.page, prev.fitMode, rotation, prev.scale, printer);
        return { ...prev, rotation };
      });
    },
    [loadPreview, printer]
  );

  const setFitMode = useCallback(
    (fitMode: FitMode) => {
      setState((prev) => {
        if (!prev.file) return { ...prev, fitMode };
        loadPreview(prev.file, prev.page, fitMode, prev.rotation, prev.scale, printer);
        return { ...prev, fitMode };
      });
    },
    [loadPreview, printer]
  );

  const setScale = useCallback(
    (scale: number) => {
      const clamped = Math.max(0.5, Math.min(1.5, scale));
      setState((prev) => {
        if (!prev.file) return { ...prev, scale: clamped };
        loadPreview(prev.file, prev.page, prev.fitMode, prev.rotation, clamped, printer);
        return { ...prev, scale: clamped };
      });
    },
    [loadPreview, printer]
  );

  const setPrintAllPages = useCallback((printAllPages: boolean) => {
    setState((prev) => ({ ...prev, printAllPages }));
  }, []);

  const print = useCallback(async () => {
    if (!state.file) return;
    setState((prev) => ({ ...prev, printing: true, error: null, printSuccess: null }));
    try {
      const result = await apiClient.printShippingLabel(state.file, {
        page: state.page,
        copies: state.copies,
        fit_mode: state.fitMode,
        rotation: state.rotation,
        scale: state.scale,
        printer,
        print_all_pages: state.printAllPages,
      });
      setState((prev) => ({
        ...prev,
        printing: false,
        printSuccess: `已打印 ${result.pages_printed} 页 × ${result.copies} 份 · ${result.queue ?? "打印机"}`,
      }));
    } catch (err) {
      setState((prev) => ({
        ...prev,
        printing: false,
        error: err instanceof ApiError ? err.message : "打印失败",
      }));
    }
  }, [
    state.file,
    state.page,
    state.copies,
    state.fitMode,
    state.rotation,
    state.scale,
    state.printAllPages,
    printer,
  ]);

  return {
    ...state,
    setFile,
    clearFile,
    setPage,
    setCopies,
    setRotation,
    setFitMode,
    setScale,
    setPrintAllPages,
    print,
  };
}
