"use client";

import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api-client";
import type { TemplateSummary } from "@/types/api";

interface TemplatesState {
  templates: TemplateSummary[];
  loading: boolean;
  error: string | null;
}

/** 拉取模板列表，供模板选择器使用。 */
export function useTemplates() {
  const [state, setState] = useState<TemplatesState>({
    templates: [],
    loading: true,
    error: null,
  });

  useEffect(() => {
    let cancelled = false;

    apiClient
      .listTemplates()
      .then((templates) => {
        if (!cancelled) setState({ templates, loading: false, error: null });
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setState({
            templates: [],
            loading: false,
            error: err instanceof Error ? err.message : "加载模板失败",
          });
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return state;
}
