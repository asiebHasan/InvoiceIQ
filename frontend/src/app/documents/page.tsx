'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import type { Document, DocumentListResponse } from '@/lib/types';
import DocumentTable from '@/components/documents/DocumentTable';
import DocumentFilters from '@/components/documents/DocumentFilters';

export default function DocumentsPage() {
  const [data, setData] = useState<DocumentListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState<Record<string, string>>({});

  useEffect(() => {
    setLoading(true);
    api.listDocuments({ ...filters, page: String(page), size: '20' })
      .then(setData)
      .finally(() => setLoading(false));
  }, [page, filters]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Documents</h1>
        <Link href="/upload" className="px-4 py-2 bg-brand-600 text-white rounded-lg text-sm font-medium hover:bg-brand-700">
          Upload New
        </Link>
      </div>
      <DocumentFilters filters={filters} onChange={setFilters} />
      {loading ? (
        <div className="text-center py-12 text-gray-500">Loading...</div>
      ) : data ? (
        <>
          <DocumentTable documents={data.documents} />
          {data.pages > 1 && (
            <div className="flex items-center justify-center gap-4">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-3 py-1 text-sm border rounded disabled:opacity-50"
              >
                Previous
              </button>
              <span className="text-sm text-gray-600">Page {data.page} of {data.pages}</span>
              <button
                onClick={() => setPage((p) => Math.min(data.pages, p + 1))}
                disabled={page === data.pages}
                className="px-3 py-1 text-sm border rounded disabled:opacity-50"
              >
                Next
              </button>
            </div>
          )}
        </>
      ) : (
        <div className="text-center py-12 text-gray-500">No documents found</div>
      )}
    </div>
  );
}
