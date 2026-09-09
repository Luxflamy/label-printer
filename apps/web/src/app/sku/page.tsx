"use client";

import { useState } from "react";
import { PrinterPicker } from "@/components/printer-picker";
import { SkuHistoryPanel } from "@/components/sku-history-panel";
import { SkuInput } from "@/components/sku-input";
import { StatusBanner } from "@/components/status-banner";
import { usePrinters } from "@/hooks/use-printers";
import { useSkuHistory } from "@/hooks/use-sku-history";
import { useSkuPrint } from "@/hooks/use-sku-print";
import { SKU_LABEL_PREFERRED_PRINTER } from "@/lib/config";

export default function SkuLabelPage() {
  const [sku, setSku] = useState("");
  const [copies, setCopies] = useState(1);

  const {
    printers,
    selectedQueue,
    loading: printersLoading,
    selecting: printerSelecting,
    error: printersError,
    lastUpdated,
    selectPrinter,
    refresh: refreshPrinters,
  } = usePrinters({ preferredQueue: SKU_LABEL_PREFERRED_PRINTER });

  // 两个实例各司其职：一个驱动输入框补全，一个驱动右侧查询面板
  const suggestions = useSkuHistory(8);
  const history = useSkuHistory(50);

  const { printing, result, error, print, reset } = useSkuPrint(selectedQueue);

  const handleSkuChange = (value: string) => {
    setSku(value);
    suggestions.search(value);
    if (result || error) reset();
  };

  const handlePrint = async () => {
    const printed = await print(sku, copies);
    if (!printed) return;
    setSku("");
    history.refresh();
    suggestions.refresh();
  };

  const canPrint = sku.trim().length > 0 && !!selectedQueue && !printing;

  return (
    <main className="mx-auto flex w-full max-w-5xl flex-col gap-5 px-6 py-8">
      <header>
        <h1 className="text-2xl font-semibold text-zinc-900 dark:text-zinc-100">
          自定义标签
        </h1>
        <p className="mt-1 text-sm text-zinc-500">
          手动输入 SKU 打印 50×30mm 小标签，打印过的 SKU 会自动记录，可随时查询复用
        </p>
      </header>

      {error && <StatusBanner kind="error" message={error} />}
      {result && (
        <StatusBanner
          kind="success"
          message={`已打印「${result.sku}」× ${result.copies} 张 · 累计 ${result.print_count} 次 · ${
            result.queue ?? "打印机"
          }`}
        />
      )}

      <div className="grid gap-5 md:grid-cols-2">
        {/* 左：打印 */}
        <section className="flex flex-col gap-4 rounded-lg border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
          <PrinterPicker
            printers={printers}
            selectedQueue={selectedQueue}
            loading={printersLoading}
            selecting={printerSelecting}
            error={printersError}
            lastUpdated={lastUpdated}
            onSelect={selectPrinter}
            onRefresh={refreshPrinters}
          />

          <SkuInput
            value={sku}
            suggestions={suggestions.items}
            disabled={printing}
            onChange={handleSkuChange}
            onPick={(picked) => {
              setSku(picked);
              if (result || error) reset();
            }}
            onSubmit={handlePrint}
          />

          <label className="flex flex-col gap-1">
            <span className="text-xs font-medium text-zinc-500">份数</span>
            <input
              type="number"
              min={1}
              max={99}
              value={copies}
              disabled={printing}
              onChange={(e) =>
                setCopies(Math.max(1, Math.min(99, Number(e.target.value) || 1)))
              }
              className="w-24 rounded-md border border-zinc-300 px-3 py-1.5 text-sm outline-none focus:border-zinc-900 disabled:opacity-50 dark:border-zinc-700 dark:bg-zinc-900 dark:focus:border-zinc-100"
            />
          </label>

          <button
            type="button"
            onClick={handlePrint}
            disabled={!canPrint}
            className="w-full rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {printing
              ? "打印中…"
              : !selectedQueue
              ? "请先选择打印机"
              : sku.trim().length === 0
              ? "请输入 SKU"
              : `打印 ${copies} 张`}
          </button>
        </section>

        {/* 右：历史查询 */}
        <section className="flex max-h-[32rem] flex-col rounded-lg border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
          <SkuHistoryPanel
            items={history.items}
            loading={history.loading}
            error={history.error}
            onSearch={history.search}
            onPick={(picked) => {
              setSku(picked);
              if (result || error) reset();
            }}
            onRemove={history.remove}
          />
        </section>
      </div>
    </main>
  );
}
