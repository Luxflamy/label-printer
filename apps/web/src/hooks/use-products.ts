"use client";

import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api-client";
import type { ProductItem } from "@/types/api";

interface State {
  products: ProductItem[];
  loading: boolean;
  error: string | null;
}

/** 按商品库加载商品列表，storeId 变化时重新拉取。 */
export function useProducts(storeId: string | null) {
  const [state, setState] = useState<State>({ products: [], loading: true, error: null });

  useEffect(() => {
    if (!storeId) {
      setState({ products: [], loading: false, error: null });
      return;
    }

    setState({ products: [], loading: true, error: null });
    apiClient
      .listProducts(storeId)
      .then((data) => setState({ products: data, loading: false, error: null }))
      .catch((err) =>
        setState({ products: [], loading: false, error: String(err.message ?? err) })
      );
  }, [storeId]);

  return state;
}
