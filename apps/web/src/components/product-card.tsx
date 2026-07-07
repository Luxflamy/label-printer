"use client";

import type { ProductItem } from "@/types/api";

interface Props {
  product: ProductItem;
  onDragStart: (product: ProductItem) => void;
  onClick: (product: ProductItem) => void;
}

/** 商品库中的单张卡片，支持拖拽和点击添加。 */
export function ProductCard({ product, onDragStart, onClick }: Props) {
  return (
    <div
      draggable
      onDragStart={(e) => {
        e.dataTransfer.setData("application/json", JSON.stringify(product));
        e.dataTransfer.effectAllowed = "copy";
        onDragStart(product);
      }}
      onClick={() => onClick(product)}
      title="拖动或点击添加到队列"
      className="group flex cursor-grab flex-col gap-1 rounded-lg border border-zinc-200 bg-white p-3 shadow-sm transition-shadow hover:shadow-md active:cursor-grabbing dark:border-zinc-700 dark:bg-zinc-900"
    >
      <div className="flex items-center justify-between gap-2">
        <span className="truncate font-mono text-xs font-semibold text-zinc-800 dark:text-zinc-100">
          {product.sku}
        </span>
        {product.qty > 0 && (
          <span className="shrink-0 rounded bg-emerald-50 px-1.5 py-0.5 text-xs text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400">
            库存 {product.qty}
          </span>
        )}
      </div>
      <p className="line-clamp-1 text-xs text-zinc-500 dark:text-zinc-400">
        {product.short_title || product.product_name}
      </p>
      <p className="font-mono text-xs text-zinc-400 dark:text-zinc-500">{product.fnsku}</p>
    </div>
  );
}
