"use client";

import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api-client";
import type { ProductStoreSummary } from "@/types/api";

const STORAGE_KEY = "label-printer-product-store";

interface State {
  stores: ProductStoreSummary[];
  selectedStore: string | null;
  defaultStore: string | null;
  loading: boolean;
  error: string | null;
}

/** 加载可用商品库列表，并记住上次选择的库。 */
export function useProductStores() {
  const [state, setState] = useState<State>({
    stores: [],
    selectedStore: null,
    defaultStore: null,
    loading: true,
    error: null,
  });

  useEffect(() => {
    apiClient
      .listProductStores()
      .then((data) => {
        const saved =
          typeof window !== "undefined" ? localStorage.getItem(STORAGE_KEY) : null;
        const validSaved = data.stores.some((s) => s.id === saved) ? saved : null;
        const initial = validSaved ?? data.default_store ?? data.stores[0]?.id ?? null;
        setState({
          stores: data.stores,
          selectedStore: initial,
          defaultStore: data.default_store,
          loading: false,
          error: null,
        });
      })
      .catch((err) =>
        setState({
          stores: [],
          selectedStore: null,
          defaultStore: null,
          loading: false,
          error: String(err.message ?? err),
        })
      );
  }, []);

  const selectStore = (storeId: string) => {
    localStorage.setItem(STORAGE_KEY, storeId);
    setState((prev) => ({ ...prev, selectedStore: storeId }));
  };

  return { ...state, selectStore };
}
