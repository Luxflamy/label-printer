/** 本地 API 地址；开发环境可用 apps/web/.env.local 覆盖。 */
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8765";

/** 运货标签页默认打印机 */
export const SHIPPING_PREFERRED_PRINTER = "TSC_TL340";

/** 批量打印页默认打印机 */
export const BATCH_PREFERRED_PRINTER = "TSC_TE344";

/** 自定义 SKU 小标签页默认打印机（与批量打印同为 50×30mm 小标签机） */
export const SKU_LABEL_PREFERRED_PRINTER = BATCH_PREFERRED_PRINTER;
