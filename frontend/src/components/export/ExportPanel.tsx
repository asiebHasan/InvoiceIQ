'use client';

import { useState } from 'react';
import { api } from '@/lib/api';

export default function ExportPanel() {
  const [docType, setDocType] = useState('');
  const [format, setFormat] = useState('csv');

  const handleExport = () => {
    const params: Record<string, string> = {};
    if (docType) params.type = docType;

    const url = format === 'csv' ? api.exportCsv(params) : api.exportExcel(params);
    window.open(url, '_blank');
  };

  return (
    <div className="card p-6 max-w-lg">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Export Data</h2>
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Document Type</label>
          <select
            value={docType}
            onChange={(e) => setDocType(e.target.value)}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
          >
            <option value="">All Types</option>
            <option value="invoice">Invoices</option>
            <option value="receipt">Receipts</option>
            <option value="purchase_order">Purchase Orders</option>
            <option value="bank_statement">Bank Statements</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Format</label>
          <div className="flex gap-4">
            <label className="flex items-center gap-2 text-sm">
              <input type="radio" value="csv" checked={format === 'csv'} onChange={(e) => setFormat(e.target.value)} />
              CSV
            </label>
            <label className="flex items-center gap-2 text-sm">
              <input type="radio" value="excel" checked={format === 'excel'} onChange={(e) => setFormat(e.target.value)} />
              Excel
            </label>
          </div>
        </div>
        <button
          onClick={handleExport}
          className="w-full px-4 py-2 bg-brand-600 text-white rounded-lg text-sm font-medium hover:bg-brand-700"
        >
          Download Export
        </button>
      </div>
    </div>
  );
}
