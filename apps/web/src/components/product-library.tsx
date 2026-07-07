"use client";

import { useMemo, useState } from "react";
import { ProductCard } from "./product-card";
import type { ProductItem } from "@/types/api";

interface Props {
  products: ProductItem[];
  loading: boolean;
  error: string | null;
  onAdd: (product: ProductItem) => void;
  onDragStart: (product: ProductItem) => void;
}

/** 左侧商品库面板：搜索 + 卡片列表。库选择在页面顶栏由 StorePicker 负责。 */
export function ProductLibrary({ products, loading, error, onAdd, onDragStart }: Props) {
  const [query, setQuery] = useState("");

  const filtered = useMemo(() => {
    if (!query.trim()) return products;
    const kw = query.toLowerCase();
    return products.filter(
      (p) =>
        p.sku.toLowerCase().includes(kw) ||
        p.fnsku.toLowerCase().includes(kw) ||
        p.short_title.toLowerCase().includes(kw) ||
        p.product_name.toLowerCase().includes(kw)
    );
  }, [products, query]);

  return (
    <div className="flex h-full flex-col gap-3">
      <div className="flex items-center gap-2">
        <input
          type="search"
          placeholder="搜索 SKU / FNSKU / 标题…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="w-full rounded-md border border-zinc-200 bg-white px-3 py-2 text-sm placeholder:text-zinc-400 focus:border-blue-400 focus:outline-none dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100"
        />
        {query && (
          <button
            type="button"
            onClick={() => setQuery("")}
            className="shrink-0 rounded-md px-2 py-1.5 text-xs text-zinc-500 hover:bg-zinc-100 dark:hover:bg-zinc-800"
          >
            清空
          </button>
        )}
      </div>

      <p className="text-xs text-zinc-400">
        {loading ? "加载中…" : `共 ${filtered.length} 条`}
        {!loading && query && ` · 关键词「${query}」`}
      </p>

      {error && (
        <div className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-600 dark:bg-red-900/20 dark:text-red-400">
          {error}
        </div>
      )}

      <div className="flex-1 overflow-y-auto pr-1">
        <div className="grid grid-cols-1 gap-2">
          {filtered.map((p) => (
            <ProductCard
              key={p.id}
              product={p}
              onDragStart={onDragStart}
              onClick={onAdd}
            />
          ))}
          {!loading && filtered.length === 0 && (
            <p className="py-8 text-center text-sm text-zinc-400">没有匹配的商品</p>
          )}
        </div>
      </div>
    </div>
  );
}
