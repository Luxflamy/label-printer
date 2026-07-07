"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { apiClient } from "@/lib/api-client";
import type {
  AutoFeedData,
  CalibrationPreviewData,
  CalibrationProfile,
  FeedStrategy,
  MediaType,
  StockSpec,
} from "@/types/api";

const EMPTY_PROFILE: CalibrationProfile = {
  reference_x_dots: 0,
  reference_y_dots: 0,
  gap_offset_mm: 0,
};

const NUDGE_DOTS = 1;

export type NudgeDirection = "up" | "down" | "left" | "right";

interface CalibrationState {
  stocks: StockSpec[];
  profile: CalibrationProfile;
  preview: CalibrationPreviewData | null;
  loading: boolean;
  previewing: boolean;
  saving: boolean;
  printing: boolean;
  autoFeeding: boolean;
  feedResult: AutoFeedData | null;
  error: string | null;
  saved: boolean;
}

export function useCalibration(printer: string | null, stockCode: string | null) {
  const [state, setState] = useState<CalibrationState>({
    stocks: [],
    profile: EMPTY_PROFILE,
    preview: null,
    loading: true,
    previewing: false,
    saving: false,
    printing: false,
    autoFeeding: false,
    feedResult: null,
    error: null,
    saved: false,
  });
  const mounted = useRef(true);
  const previewTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    mounted.current = true;
    apiClient
      .listCalibrationStocks()
      .then((data) => {
        if (!mounted.current) return;
        setState((prev) => ({ ...prev, stocks: data.stocks, loading: false }));
      })
      .catch((err) => {
        if (!mounted.current) return;
        setState((prev) => ({
          ...prev,
          loading: false,
          error: err instanceof Error ? err.message : "加载纸张规格失败",
        }));
      });
    return () => {
      mounted.current = false;
    };
  }, []);

  useEffect(() => {
    if (!printer || !stockCode) return;
    setState((prev) => ({
      ...prev,
      loading: true,
      error: null,
      saved: false,
      feedResult: null,
    }));
    apiClient
      .getCalibration(printer, stockCode)
      .then((data) => {
        if (!mounted.current) return;
        setState((prev) => ({
          ...prev,
          profile: data.profile,
          loading: false,
        }));
      })
      .catch((err) => {
        if (!mounted.current) return;
        setState((prev) => ({
          ...prev,
          loading: false,
          error: err instanceof Error ? err.message : "加载校准配置失败",
        }));
      });
  }, [printer, stockCode]);

  const refreshPreview = useCallback(
    async (profile: CalibrationProfile) => {
      if (!printer || !stockCode) return;
      setState((prev) => ({ ...prev, previewing: true, error: null }));
      try {
        const data = await apiClient.previewCalibration(printer, stockCode, profile);
        if (!mounted.current) return;
        setState((prev) => ({ ...prev, preview: data, previewing: false }));
      } catch (err) {
        if (!mounted.current) return;
        setState((prev) => ({
          ...prev,
          previewing: false,
          error: err instanceof Error ? err.message : "预览失败",
        }));
      }
    },
    [printer, stockCode]
  );

  useEffect(() => {
    if (!printer || !stockCode || state.loading) return;
    if (previewTimer.current) clearTimeout(previewTimer.current);
    previewTimer.current = setTimeout(() => {
      refreshPreview(state.profile);
    }, 300);
    return () => {
      if (previewTimer.current) clearTimeout(previewTimer.current);
    };
  }, [printer, stockCode, state.profile, state.loading, refreshPreview]);

  const adjustProfile = useCallback((patch: Partial<CalibrationProfile>) => {
    setState((prev) => ({
      ...prev,
      profile: { ...prev.profile, ...patch },
      saved: false,
    }));
  }, []);

  const nudge = useCallback(
    (direction: NudgeDirection) => {
      setState((prev) => {
        const p = prev.profile;
        const next = { ...p };
        switch (direction) {
          case "up":
            next.reference_y_dots = p.reference_y_dots + NUDGE_DOTS;
            break;
          case "down":
            next.reference_y_dots = p.reference_y_dots - NUDGE_DOTS;
            break;
          case "left":
            next.reference_x_dots = p.reference_x_dots + NUDGE_DOTS;
            break;
          case "right":
            next.reference_x_dots = p.reference_x_dots - NUDGE_DOTS;
            break;
        }
        return { ...prev, profile: next, saved: false };
      });
    },
    []
  );

  const save = useCallback(async () => {
    if (!printer || !stockCode) return;
    setState((prev) => ({ ...prev, saving: true, error: null }));
    try {
      const data = await apiClient.saveCalibration(printer, stockCode, state.profile);
      if (!mounted.current) return;
      setState((prev) => ({
        ...prev,
        profile: data.profile,
        saving: false,
        saved: true,
      }));
    } catch (err) {
      if (!mounted.current) return;
      setState((prev) => ({
        ...prev,
        saving: false,
        error: err instanceof Error ? err.message : "保存失败",
      }));
    }
  }, [printer, stockCode, state.profile]);

  const printTest = useCallback(async () => {
    if (!printer || !stockCode) return;
    setState((prev) => ({ ...prev, printing: true, error: null }));
    try {
      await apiClient.printCalibration(printer, stockCode, state.profile);
      if (!mounted.current) return;
      setState((prev) => ({ ...prev, printing: false }));
    } catch (err) {
      if (!mounted.current) return;
      setState((prev) => ({
        ...prev,
        printing: false,
        error: err instanceof Error ? err.message : "打印失败",
      }));
    }
  }, [printer, stockCode, state.profile]);

  const autoFeedCalibrate = useCallback(
    async (
      mediaType: MediaType = "gap",
      strategy: FeedStrategy = "gapdetect",
      printTestAfter = false
    ) => {
      if (!printer || !stockCode) return;
      setState((prev) => ({
        ...prev,
        autoFeeding: true,
        error: null,
        feedResult: null,
        saved: false,
      }));
      try {
        const data = await apiClient.autoFeedCalibrate(printer, stockCode, {
          media_type: mediaType,
          strategy,
          print_test_after: printTestAfter,
        });
        if (!mounted.current) return;
        setState((prev) => ({ ...prev, autoFeeding: false, feedResult: data }));
      } catch (err) {
        if (!mounted.current) return;
        setState((prev) => ({
          ...prev,
          autoFeeding: false,
          error: err instanceof Error ? err.message : "走纸校准失败",
        }));
      }
    },
    [printer, stockCode]
  );

  const clearFeedResult = useCallback(() => {
    setState((prev) => ({ ...prev, feedResult: null }));
  }, []);

  return {
    ...state,
    adjustProfile,
    nudge,
    save,
    printTest,
    autoFeedCalibrate,
    clearFeedResult,
    refreshPreview: () => refreshPreview(state.profile),
  };
}
