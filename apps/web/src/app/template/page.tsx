"use client";

import { useEffect, useState } from "react";
import { LabelPreview } from "@/components/label-preview";
import { PrintButton } from "@/components/print-button";
import { PrinterStatus } from "@/components/printer-status";
import { StatusBanner } from "@/components/status-banner";
import { TemplatePicker } from "@/components/template-picker";
import { VariableForm } from "@/components/variable-form";
import { usePrintActions } from "@/hooks/use-print-actions";
import { useTemplateDetail } from "@/hooks/use-template-detail";
import { useTemplates } from "@/hooks/use-templates";

export default function TemplatePrintPage() {
  const { templates, loading: templatesLoading, error: templatesError } = useTemplates();
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null);
  const { detail, loading: detailLoading } = useTemplateDetail(selectedTemplate);
  const [variables, setVariables] = useState<Record<string, string>>({});

  const {
    imagePreview,
    tsplPreview,
    printState,
    previewImage,
    previewTspl,
    printLabel,
    resetPrintState,
  } = usePrintActions();

  useEffect(() => {
    if (!selectedTemplate && templates.length > 0) {
      const preferred =
        templates.find((t) => t.default) ??
        templates.find((t) => t.id === "xiaobiaoqian") ??
        templates.find((t) => t.variables.length > 0);
      setSelectedTemplate((preferred ?? templates[0]).id);
    }
  }, [templates, selectedTemplate]);

  useEffect(() => {
    if (detail) {
      const next: Record<string, string> = {};
      for (const name of detail.variables) next[name] = "";
      setVariables(next);
    }
  }, [detail]);

  const handleSelectTemplate = (name: string) => {
    setSelectedTemplate(name);
    resetPrintState();
  };

  const buildPayload = () => ({
    template: selectedTemplate ?? "",
    variables,
  });

  const handlePreview = () => {
    if (!selectedTemplate) return;
    const payload = buildPayload();
    previewImage(payload);
    previewTspl(payload);
  };

  const handlePrint = () => {
    if (!selectedTemplate) return;
    printLabel(buildPayload());
  };

  const canSubmit =
    !!selectedTemplate &&
    !!detail &&
    detail.variables.every((name) => (variables[name] ?? "").trim() !== "");

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-col gap-6 px-6 py-10">
      <header className="flex flex-col gap-1">
        <h1 className="text-2xl font-semibold">模板打印</h1>
        <p className="text-sm text-zinc-500">YAML 模板 + 变量，适合小标签等自定义排版</p>
      </header>

      <PrinterStatus />

      <section className="flex flex-col gap-3">
        <h2 className="text-sm font-medium text-zinc-500">1. 选择模板</h2>
        {templatesError ? (
          <StatusBanner kind="error" message={templatesError} />
        ) : (
          <TemplatePicker
            templates={templates}
            selected={selectedTemplate}
            onSelect={handleSelectTemplate}
            loading={templatesLoading}
          />
        )}
      </section>

      {selectedTemplate && (
        <section className="flex flex-col gap-3">
          <h2 className="text-sm font-medium text-zinc-500">2. 填写内容</h2>
          {detailLoading && <p className="text-sm text-zinc-500">加载模板详情…</p>}
          {detail && (
            <VariableForm
              variables={detail.variables}
              values={variables}
              onChange={(name, value) => setVariables((prev) => ({ ...prev, [name]: value }))}
            />
          )}
        </section>
      )}

      {selectedTemplate && (
        <section className="flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-medium text-zinc-500">3. 预览与打印</h2>
            <button
              type="button"
              onClick={handlePreview}
              disabled={!canSubmit || imagePreview.loading || tsplPreview.loading}
              className="rounded-md bg-zinc-100 px-3 py-1 text-sm font-medium text-zinc-700 hover:bg-zinc-200 disabled:cursor-not-allowed disabled:opacity-40 dark:bg-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-700"
            >
              {imagePreview.loading ? "生成中…" : "预览标签"}
            </button>
          </div>

          <LabelPreview
            imageResult={imagePreview.result}
            imageLoading={imagePreview.loading}
            imageError={imagePreview.error}
            tspl={tsplPreview.result?.tspl ?? null}
            tsplLoading={tsplPreview.loading}
            tsplError={tsplPreview.error}
          />

          <div className="flex items-center gap-4">
            <PrintButton loading={printState.loading} disabled={!canSubmit} onClick={handlePrint} />
            {!canSubmit && <span className="text-sm text-zinc-400">请先填写完所有字段</span>}
          </div>

          {printState.result && (
            <StatusBanner
              kind="success"
              message={`打印成功：模板 ${printState.result.template} · 打印机 ${
                printState.result.queue ?? "未知"
              }`}
            />
          )}
          {printState.error && <StatusBanner kind="error" message={printState.error} />}
        </section>
      )}
    </div>
  );
}
