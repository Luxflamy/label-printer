"use client";

import type { ProductStoreSummary } from "@/types/api";

interface StorePickerProps {
  stores: ProductStoreSummary[];
  selected: string | null;
  onSelect: (storeId: string) => void;
  loading?: boolean;
  defaultStore?: string | null;
}

export function StorePicker({
  stores,
  selected,
  onSelect,
  loading,
  defaultStore,
}: StorePickerProps) {
  if (loading) {
    return <p className="text-xs text-zinc-500">正在加载商品库…</p>;
  }

  if (stores.length === 0) {
    return <p className="text-xs text-zinc-500">暂无可用商品库</p>;
  }

  return (
    <div className="flex flex-wrap gap-1">
      {stores.map((store) => {
        const isActive = store.id === selected;
        const isDefault = store.id === defaultStore;
        return (
          <button
            key={store.id}
            type="button"
            onClick={() => onSelect(store.id)}
            className={`flex items-center gap-1 rounded-md border px-2 py-0.5 text-left transition-colors ${
              isActive
                ? "border-zinc-900 bg-zinc-900 text-white dark:border-zinc-100 dark:bg-zinc-100 dark:text-zinc-900"
                : "border-zinc-200 bg-white text-zinc-700 hover:border-zinc-400 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-300 dark:hover:border-zinc-500"
            }`}
          >
            <span className="text-xs font-medium">{store.name}</span>
            {isDefault && (
              <span
                className={`text-[10px] ${isActive ? "text-zinc-300 dark:text-zinc-600" : "text-zinc-400"}`}
              >
                默认
              </span>
            )}
            <span
              className={`rounded px-1 py-px text-[10px] leading-none ${
                isActive
                  ? "bg-white/20 text-white dark:bg-black/20 dark:text-zinc-900"
                  : "bg-zinc-100 text-zinc-500 dark:bg-zinc-800 dark:text-zinc-400"
              }`}
            >
              {store.product_count} 条
            </span>
          </button>
        );
      })}
    </div>
  );
}
