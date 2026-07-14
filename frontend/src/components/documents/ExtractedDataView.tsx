'use client';

import type { ExtractedData } from '@/lib/types';
import { formatCurrency, formatDate } from '@/lib/utils';

interface Props {
  data: ExtractedData;
  showRaw: boolean;
  onToggleRaw: () => void;
}

export default function ExtractedDataView({ data, showRaw, onToggleRaw }: Props) {
  return (
    <div className="card p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">Extracted Data</h2>
        <button onClick={onToggleRaw} className="text-sm text-brand-600 hover:underline">
          {showRaw ? 'Hide' : 'Show'} Raw Text
        </button>
      </div>

      {showRaw && data.raw_text && (
        <pre className="bg-gray-50 rounded-lg p-4 text-xs text-gray-700 overflow-auto max-h-64 mb-4 whitespace-pre-wrap">
          {data.raw_text}
        </pre>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Section title="Vendor">
          <Field label="Name" value={data.vendor_name} />
          <Field label="Address" value={data.vendor_address} />
        </Section>
        <Section title="Customer">
          <Field label="Name" value={data.customer_name} />
          <Field label="Address" value={data.customer_address} />
        </Section>
        <Section title="Invoice Details">
          <Field label="Invoice Number" value={data.invoice_number} />
          <Field label="Invoice Date" value={formatDate(data.invoice_date)} />
          <Field label="Due Date" value={formatDate(data.due_date)} />
          <Field label="Payment Terms" value={data.payment_terms} />
        </Section>
        <Section title="Amounts">
          <Field label="Subtotal" value={formatCurrency(data.subtotal)} />
          <Field label="Tax" value={formatCurrency(data.tax_amount)} />
          <Field label="Total" value={formatCurrency(data.total_amount)} />
          <Field label="Currency" value={data.currency} />
        </Section>
      </div>

      {data.line_items && data.line_items.length > 0 && (
        <div className="mt-6">
          <h3 className="text-sm font-semibold text-gray-700 mb-2">Line Items</h3>
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="text-left px-3 py-2 text-xs font-medium text-gray-500">Description</th>
                <th className="text-right px-3 py-2 text-xs font-medium text-gray-500">Qty</th>
                <th className="text-right px-3 py-2 text-xs font-medium text-gray-500">Unit Price</th>
                <th className="text-right px-3 py-2 text-xs font-medium text-gray-500">Total</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data.line_items.map((item, i) => (
                <tr key={i}>
                  <td className="px-3 py-2">{item.description}</td>
                  <td className="px-3 py-2 text-right">{item.quantity}</td>
                  <td className="px-3 py-2 text-right">{formatCurrency(item.unit_price)}</td>
                  <td className="px-3 py-2 text-right">{formatCurrency(item.total)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="mt-4 flex gap-4 text-xs text-gray-500">
        <span>Method: {data.extraction_method || '-'}</span>
        <span>Confidence: {data.extraction_confidence ? `${(data.extraction_confidence * 100).toFixed(0)}%` : '-'}</span>
      </div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h3 className="text-sm font-semibold text-gray-700 mb-2">{title}</h3>
      <div className="space-y-1">{children}</div>
    </div>
  );
}

function Field({ label, value }: { label: string; value: string | null | undefined }) {
  return (
    <div className="flex gap-2">
      <span className="text-xs text-gray-500 w-28 shrink-0">{label}:</span>
      <span className="text-sm text-gray-900">{value || '-'}</span>
    </div>
  );
}
