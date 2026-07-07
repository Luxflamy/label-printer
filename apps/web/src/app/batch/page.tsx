"use client";

import { useCallback, useEffect, useState } from "react";
import { PrintQueue } from "@/components/print-queue";
import { ProductLibrary } from "@/components/product-library";
import { StatusBanner } from "@/components/status-banner";
import { StorePicker } from "@/components/store-picker";
import { TemplatePicker } from "@/components/template-picker";
import { useBatchPrint } from "@/hooks/use-batch-print";
import { usePrintQueue } from "@/hooks/use-print-queue";
import { useProductStores } from "@/hooks/use-product-stores";
import { useProducts } from "@/hooks/use-products";
import { useTemplates } from "@/hooks/use-templates";

export default function BatchPage() {
  /* ---- 模板 ---- */
  const { templates, loading: tplLoading } = useTemplates();
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null);

  useEffect(() => {
    if (!selectedTemplate && templates.length > 0) {
      const preferred =
        templates.find((t) => t.default) ??
        templates.find((t) => t.id === "xiaobiaoqian") ??
        templates[0];
      setSelectedTemplate(preferred.id);
    }
  }, [templates, selectedTemplate]);

  /* ---- 商品库 ---- */
  const {
    stores,
    selectedStore,
    defaultStore,
    loading: storesLoading,
    error: storesError,
    selectStore,
  } = useProductStores();
  const { products, loading: productsLoading, error: productsError } = useProducts(selectedStore);

  /* ---- 打印队列 ---- */
  const { queue, addToQueue, setCopies, removeFromQueue, clearQueue, reorderQueue } = usePrintQueue();

  /* ---- 批量打印 ---- */
  const { loading: printing, result: printResult, error: printError, print, reset } = useBatchPrint();

  const handleStoreChange = (storeId: string) => {
    if (storeId === selectedStore) return;
    selectStore(storeId);
    clearQueue();
    reset();
  };

  /* ---- 拖拽来自商品库（DataTransfer 存 JSON，在 ProductCard 中已处理） ---- */
  const handleDragStart = useCallback(() => {
    // ProductCard 在原生 dragstart 中已通过 e.dataTransfer.setData 写入数据
  }, []);

  const handlePrint = () => {
    if (!selectedTemplate || !selectedStore) return;
    reset();
    print(selectedTemplate, selectedStore, queue);
  };

  const totalSheets = queue.reduce((s, e) => s + e.copies, 0);

  return (
    <div className="flex h-[calc(100vh-49px)] flex-col gap-0 overflow-hidden">
      {/* 上方：模板 + 商品库选择 */}
      <div className="shrink-0 border-b border-zinc-200 bg-white dark:border-zinc-800 dark:bg-black">
        <div className="mx-auto flex max-w-7xl flex-col gap-1.5 px-4 py-2">
          <div className="flex items-center gap-2.5">
            <h2 className="w-14 shrink-0 text-xs font-medium text-zinc-500">打印模板</h2>
            <TemplatePicker
              templates={templates}
              selected={selectedTemplate}
              onSelect={(id) => { setSelectedTemplate(id); reset(); }}
              loading={tplLoading}
            />
          </div>
          <div className="flex items-center gap-2.5">
            <h2 className="w-14 shrink-0 text-xs font-medium text-zinc-500">商品库</h2>
            <StorePicker
              stores={stores}
              selected={selectedStore}
              defaultStore={defaultStore}
              onSelect={handleStoreChange}
              loading={storesLoading}
            />
            {storesError && (
              <p className="text-xs text-red-500">{storesError}</p>
            )}
          </div>
        </div>
      </div>

      {/* 下方：左右双栏 */}
      <div className="flex min-h-0 flex-1">
        {/* 左侧：商品库 */}
        <div className="flex w-1/2 flex-col gap-0 border-r border-zinc-200 dark:border-zinc-800">
          <div className="min-h-0 flex-1 overflow-hidden px-5 py-4">
            <ProductLibrary
              products={products}
              loading={productsLoading}
              error={productsError}
              onAdd={addToQueue}
              onDragStart={handleDragStart}
            />
          </div>
        </div>

        {/* 右侧：打印队列 */}
        <div className="flex w-1/2 flex-col">
          <div className="shrink-0 border-b border-zinc-100 bg-zinc-50 px-5 py-2 dark:border-zinc-800 dark:bg-zinc-950">
            <h2 className="text-sm font-medium text-zinc-600 dark:text-zinc-400">打印队列</h2>
          </div>
          <div className="min-h-0 flex-1 overflow-hidden px-5 py-4">
            <PrintQueue
              queue={queue}
              onAdd={addToQueue}
              onCopiesChange={setCopies}
              onRemove={removeFromQueue}
              onReorder={reorderQueue}
              onClear={clearQueue}
            />
          </div>
          {/* 底部操作栏 */}
          <div className="shrink-0 border-t border-zinc-200 bg-white px-5 py-3 dark:border-zinc-800 dark:bg-black">
            {printResult && (
              <div className="mb-2 space-y-1">
                <StatusBanner
                  kind={printResult.failed === 0 ? "success" : "warning"}
                  message={`打印完成：成功 ${printResult.succeeded} / 共 ${printResult.total} 条${
                    printResult.failed > 0 ? `，${printResult.failed} 条失败（已跳过）` : ""
                  }`}
                />
                {printResult.failed > 0 && (
                  <div className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 dark:border-amber-800 dark:bg-amber-900/20">
                    <p className="mb-1 text-xs font-semibold text-amber-700 dark:text-amber-400">
                      失败明细
                    </p>
                    <ul className="space-y-0.5">
                      {printResult.results
                        .filter((r) => !r.ok)
                        .map((r) => (
                          <li key={r.product_id} className="text-xs text-amber-700 dark:text-amber-300">
                            <span className="font-mono font-medium">{r.sku || r.product_id}</span>
                            {r.error && (
                              <span className="ml-1 text-amber-500 dark:text-amber-400">
                                — {r.error}
                              </span>
                            )}
                          </li>
                        ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
            {printError && (
              <div className="mb-2">
                <StatusBanner kind="error" message={printError} />
              </div>
            )}
            <button
              type="button"
              onClick={handlePrint}
              disabled={queue.length === 0 || !selectedTemplate || !selectedStore || printing}
              className="w-full rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {printing
                ? "打印中…"
                : queue.length === 0
                ? "请先添加商品到队列"
                : `批量打印 ${queue.length} 种 · ${totalSheets} 张`}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
