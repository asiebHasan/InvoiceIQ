export interface Document {
  id: string;
  filename: string;
  document_type: string;
  classification_confidence: number | null;
  status: string;
  file_size: number;
  created_at: string;
  processed_at: string | null;
  total_amount: number | null;
  anomaly_count: number;
}

export interface ExtractedData {
  id: string;
  vendor_name: string | null;
  vendor_address: string | null;
  customer_name: string | null;
  customer_address: string | null;
  invoice_number: string | null;
  invoice_date: string | null;
  due_date: string | null;
  total_amount: number | null;
  subtotal: number | null;
  tax_amount: number | null;
  currency: string | null;
  line_items: LineItem[] | null;
  payment_terms: string | null;
  raw_text: string | null;
  extraction_method: string | null;
  extraction_confidence: number | null;
}

export interface LineItem {
  description: string | null;
  quantity: number | null;
  unit_price: number | null;
  total: number | null;
}

export interface Anomaly {
  id: string;
  anomaly_type: string;
  severity: string;
  description: string;
  details: Record<string, unknown> | null;
  is_resolved: boolean;
  created_at: string;
}

export interface DocumentDetail extends Document {
  file_hash: string;
  extracted_data: ExtractedData | null;
  anomalies: Anomaly[];
}

export interface DocumentListResponse {
  documents: Document[];
  total: number;
  page: number;
  pages: number;
}

export interface DashboardStats {
  total_documents: number;
  processed_count: number;
  processing_count: number;
  failed_count: number;
  anomaly_count: number;
  by_type: Record<string, number>;
}

export interface TimelinePoint {
  date: string;
  count: number;
}

export interface ChatResponse {
  answer: string;
  sources: { filename: string; doc_id: string }[];
}
