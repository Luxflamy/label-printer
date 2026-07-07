"use client";

import { useState } from "react";
import { ApiError, apiClient } from "@/lib/api-client";
import type { LabelPreviewResult, PrintPayload, PrintResult, RenderResult } from "@/types/api";

interface ImagePreviewState {
  loading: boolean;
  result: LabelPreviewResult | null;
  error: string | null;
}

interface TsplPreviewState {
  loading: boolean;
  result: RenderResult | null;
  error: string | null;
}

interface PrintState {
  loading: boolean;
  result: PrintResult | null;
  error: string | null;
}

/** 封装"图片预览"、"TSPL 预览"与"打印"三个动作的调用状态，供页面直接消费。 */
export function usePrintActions() {
  const [imagePreview, setImagePreview] = useState<ImagePreviewState>({
    loading: false,
    result: null,
    error: null,
  });
  const [tsplPreview, setTsplPreview] = useState<TsplPreviewState>({
    loading: false,
    result: null,
    error: null,
  });
  const [printState, setPrintState] = useState<PrintState>({
    loading: false,
    result: null,
    error: null,
  });

  /** 获取标签预览图（PNG base64）。 */
  const previewImage = async (payload: Omit<PrintPayload, "copies">) => {
    setImagePreview({ loading: true, result: null, error: null });
    try {
      const result = await apiClient.renderPreview(payload);
      setImagePreview({ loading: false, result, error: null });
    } catch (err) {
      setImagePreview({
        loading: false,
        result: null,
        error: err instanceof ApiError ? err.message : "预览图生成失败",
      });
    }
  };

  /** 获取 TSPL 文本预览（折叠展示用）。 */
  const previewTspl = async (payload: PrintPayload) => {
    setTsplPreview({ loading: true, result: null, error: null });
    try {
      const result = await apiClient.render(payload);
      setTsplPreview({ loading: false, result, error: null });
    } catch (err) {
      setTsplPreview({
        loading: false,
        result: null,
        error: err instanceof ApiError ? err.message : "TSPL 生成失败",
      });
    }
  };

  const printLabel = async (payload: PrintPayload) => {
    setPrintState({ loading: true, result: null, error: null });
    try {
      const result = await apiClient.printOne(payload);
      setPrintState({ loading: false, result, error: null });
    } catch (err) {
      setPrintState({
        loading: false,
        result: null,
        error: err instanceof ApiError ? err.message : "打印失败",
      });
    }
  };

  const resetPrintState = () => setPrintState({ loading: false, result: null, error: null });

  return {
    imagePreview,
    tsplPreview,
    printState,
    previewImage,
    previewTspl,
    printLabel,
    resetPrintState,
  };
}
