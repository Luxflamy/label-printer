"use client";

import type { TemplateSummary } from "@/types/api";

interface TemplatePickerProps {
  templates: TemplateSummary[];
  selected: string | null;
  onSelect: (name: string) => void;
  loading?: boolean;
}

export function TemplatePicker({
  templates,
  selected,
  onSelect,
  loading,
}: TemplatePickerProps) {
  if (loading) {
    return <p className="text-xs text-zinc-500">正在加载模板列表…</p>;
  }

  if (templates.length === 0) {
    return <p className="text-xs text-zinc-500">暂无可用模板</p>;
  }

  return (
    <div className="flex flex-wrap gap-1">
      {templates.map((tpl) => {
        const isActive = tpl.id === selected;
        return (
          <button
            key={tpl.id}
            type="button"
            onClick={() => onSelect(tpl.id)}
            className={`flex items-center gap-1 rounded-md border px-2 py-0.5 text-left transition-colors ${
              isActive
                ? "border-zinc-900 bg-zinc-900 text-white dark:border-zinc-100 dark:bg-zinc-100 dark:text-zinc-900"
                : "border-zinc-200 bg-white text-zinc-700 hover:border-zinc-400 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-300 dark:hover:border-zinc-500"
            }`}
          >
            <span className="text-xs font-medium">{tpl.name}</span>
            {tpl.default && (
              <span className={`text-[10px] ${isActive ? "text-zinc-300 dark:text-zinc-600" : "text-zinc-400"}`}>
                默认
              </span>
            )}
            {tpl.stock_code && (
              <span
                className={`rounded px-1 py-px text-[10px] leading-none ${
                  isActive
                    ? "bg-white/20 text-white dark:bg-black/20 dark:text-zinc-900"
                    : "bg-zinc-100 text-zinc-500 dark:bg-zinc-800 dark:text-zinc-400"
                }`}
              >
                {tpl.stock_code}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}
