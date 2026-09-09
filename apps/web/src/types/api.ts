/**
 * 与 services/api/schemas.py 一一对应的 TypeScript 类型。
 * 后端返回结构变化时，先改这里，编译器会提示所有需要同步的地方。
 */

export interface ErrorInfo {
  code: string;
  message: string;
}

export interface Envelope<T> {
  ok: boolean;
  data: T | null;
  error: ErrorInfo | null;
}

export interface HealthData {
  status: string;
  service: string;
}

export interface PrinterInfo {
  name: string;
  status: string;
  selected?: boolean;
}

export interface PrinterListData {
  printers: PrinterInfo[];
  selected_queue: string | null;
}

export interface TemplateSummary {
  id: string;
  name: string;
  description: string;
  width_mm: number;
  height_mm: number;
  stock_code: string | null;
  variables: string[];
  default?: boolean;
}

export interface TemplateElement {
  id?: string;
  type: string;
  x_mm: number;
  y_mm: number;
  content?: string;
  [key: string]: unknown;
}

export interface TemplateDetail {
  id: string;
  name: string;
  description: string;
  label: {
    width_mm: number;
    height_mm: number;
    gap_mm?: number;
    direction?: number;
    [key: string]: unknown;
  };
  elements: TemplateElement[];
  meta: Record<string, unknown>;
  variables: string[];
}

export interface RenderResult {
  template: string;
  tspl: string;
  label: Record<string, unknown>;
}

export interface PrintResult {
  template: string;
  copies: number;
  queue: string | null;
}

export interface PrintPayload {
  template: string;
  variables: Record<string, string>;
  copies?: number;
  printer?: string | null;
}

export interface RenderPayload {
  template: string;
  variables: Record<string, string>;
  copies?: number;
  printer?: string | null;
}

/** POST /render/preview 响应体 */
export interface LabelPreviewResult {
  template: string;
  image_b64: string;
  width_mm: number;
  height_mm: number;
}

// ---- 商品数据 -------------------------------------------------------

export interface ProductItem {
  id: string;
  sku: string;
  fnsku: string;
  short_title: string;
  product_name: string;
  qty: number;
}

export interface ProductStoreSummary {
  id: string;
  name: string;
  product_count: number;
}

export interface ProductStoresData {
  stores: ProductStoreSummary[];
  default_store: string | null;
}

// ---- 批量打印 -------------------------------------------------------

export interface BatchItem {
  product_id: string;
  copies: number;
}

export interface BatchPrintPayload {
  template: string;
  store?: string | null;
  printer?: string | null;
  items: BatchItem[];
}

export interface BatchItemResult {
  product_id: string;
  sku: string;
  copies: number;
  ok: boolean;
  error?: string | null;
}

export interface BatchPrintData {
  total: number;
  succeeded: number;
  failed: number;
  results: BatchItemResult[];
}

// ---- 校准 -------------------------------------------------------------

export interface CalibrationProfile {
  reference_x_dots: number;
  reference_y_dots: number;
  gap_offset_mm: number;
}

export interface StockSpec {
  stock_code: string;
  name: string;
  width_mm: number;
  height_mm: number;
  gap_mm: number;
  direction: number;
}

export interface CalibrationData {
  printer: string;
  stock_code: string;
  profile: CalibrationProfile;
}

export interface CalibrationPreviewData {
  printer: string;
  stock_code: string;
  profile: CalibrationProfile;
  image_b64: string;
  tspl: string;
  width_mm: number;
  height_mm: number;
}

export type MediaType = "gap" | "blackmark";
export type FeedStrategy = "gapdetect" | "autodetect";

export interface AutoFeedData {
  printer: string;
  stock_code: string;
  media_type: MediaType;
  strategy: FeedStrategy;
  tspl: string;
  message: string;
  test_printed: boolean;
}

export type FitMode = "contain" | "cover" | "fill";

export interface ShippingLabelPreviewData {
  page_count: number;
  page: number;
  pdf_width_mm: number;
  pdf_height_mm: number;
  target_stock: string;
  target_width_mm: number;
  target_height_mm: number;
  fit_mode: FitMode;
  rotation: number;
  scale: number;
  image_b64: string;
  warnings: string[];
}

export interface ShippingLabelPrintData {
  pages_printed: number;
  copies: number;
  queue: string | null;
  stock_code: string;
}

/** 已打印过的 SKU 历史记录 */
export interface SkuRecord {
  sku: string;
  first_printed_at: string;
  last_printed_at: string;
  print_count: number;
  last_template: string | null;
}

export interface SkuHistoryData {
  items: SkuRecord[];
  total: number;
}

export interface SkuLabelPrintData {
  sku: string;
  template: string;
  copies: number;
  queue: string | null;
  print_count: number;
  first_printed_at: string;
  last_printed_at: string;
}

export interface SkuLabelPrintPayload {
  sku: string;
  template?: string | null;
  copies?: number;
  printer?: string | null;
}

/** 打印队列条目（本地状态，含 ProductItem 完整数据） */
export interface QueueEntry {
  product: ProductItem;
  copies: number;
}
