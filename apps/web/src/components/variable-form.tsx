"use client";

/** 常见字段的中文展示名；未收录的字段直接显示原始变量名。 */
const FIELD_LABELS: Record<string, string> = {
  product_name: "品名",
  sku: "SKU",
  barcode: "条码",
  remark: "备注",
};

interface VariableFormProps {
  variables: string[];
  values: Record<string, string>;
  onChange: (name: string, value: string) => void;
}

export function VariableForm({ variables, values, onChange }: VariableFormProps) {
  if (variables.length === 0) {
    return <p className="text-sm text-zinc-500">该模板不需要填写变量</p>;
  }

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
      {variables.map((name) => (
        <label key={name} className="flex flex-col gap-1 text-sm">
          <span className="font-medium text-zinc-700 dark:text-zinc-300">
            {FIELD_LABELS[name] ?? name}
          </span>
          <input
            type="text"
            value={values[name] ?? ""}
            onChange={(e) => onChange(name, e.target.value)}
            placeholder={`请输入${FIELD_LABELS[name] ?? name}`}
            className="rounded-md border border-zinc-300 px-3 py-2 outline-none focus:border-zinc-900 dark:border-zinc-700 dark:bg-zinc-900 dark:focus:border-zinc-100"
          />
        </label>
      ))}
    </div>
  );
}
