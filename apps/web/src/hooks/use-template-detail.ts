"use client";

import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api-client";
import type { TemplateDetail } from "@/types/api";

interface TemplateDetailState {
  detail: TemplateDetail | null;
  loading: boolean;
  error: string | null;
}

/** 按模板名拉取完整详情（含 elements 与 variables），name 为空时不请求。 */
export function useTemplateDetail(name: string | null) {
  const [state, setState] = useState<TemplateDetailState>({
    detail: null,
    loading: false,
    error: null,
  });

  useEffect(() => {
    if (!name) {
      setState({ detail: null, loading: false, error: null });
      return;
    }

    let cancelled = false;
    setState({ detail: null, loading: true, error: null });

    apiClient
      .getTemplate(name)
      .then((detail) => {
        if (!cancelled) setState({ detail, loading: false, error: null });
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setState({
            detail: null,
            loading: false,
            error: err instanceof Error ? err.message : "加载模板详情失败",
          });
        }
      });

    return () => {
      cancelled = true;
    };
  }, [name]);

  return state;
}
