'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import type { DocumentDetail } from '@/lib/types';
import ExtractedDataView from '@/components/documents/ExtractedDataView';
import AnomalyBadge from '@/components/documents/AnomalyBadge';
import { formatDate, formatFileSize, documentTypeColor, statusColor } from '@/lib/utils';

export default function DocumentDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const [doc, setDoc] = useState<DocumentDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [showRaw, setShowRaw] = useState(false);

  useEffect(() => {
    api.getDocument(id).then(setDoc).finally(() => setLoading(false));
  }, [id]);

  const handleReprocess = async () => {
    await api.reprocessDocument(id);
    setLoading(true);
    api.getDocument(id).then(setDoc).finally(() => setLoading(false));
  };

  if (loading) return <div className="flex items-center justify-center h-64 text-gray-500">Loading...</div>;
  if (!doc) return <div className="text-center py-12 text-gray-500">Document not found</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <Link href="/documents" className="text-sm text-brand-600 hover:underline">&larr; Back to Documents</Link>
          <h1 className="text-2xl font-bold text-gray-900 mt-1">{doc.filename}</h1>
        </div>
        <div className="flex gap-2">
          <button onClick={handleReprocess} className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-50">
            Reprocess
          </button>
          <a href={`/api/documents/${doc.id}/download`} className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-50">
            Download PDF
          </a>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-4">
        <div className="card p-4">
          <p className="text-xs text-gray-500">Type</p>
          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${documentTypeColor(doc.document_type)}`}>
            {doc.document_type}
          </span>
        </div>
        <div className="card p-4">
          <p className="text-xs text-gray-500">Status</p>
          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${statusColor(doc.status)}`}>
            {doc.status}
          </span>
        </div>
        <div className="card p-4">
          <p className="text-xs text-gray-500">Uploaded</p>
          <p className="text-sm font-medium">{formatDate(doc.created_at)}</p>
        </div>
        <div className="card p-4">
          <p className="text-xs text-gray-500">File Size</p>
          <p className="text-sm font-medium">{formatFileSize(doc.file_size)}</p>
        </div>
      </div>

      {doc.anomalies.length > 0 && (
        <div className="card p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-3">Anomalies Detected</h2>
          <div className="space-y-2">
            {doc.anomalies.map((a) => <AnomalyBadge key={a.id} anomaly={a} />)}
          </div>
        </div>
      )}

      {doc.extracted_data && (
        <ExtractedDataView data={doc.extracted_data} showRaw={showRaw} onToggleRaw={() => setShowRaw(!showRaw)} />
      )}

      {doc.status === 'processing' && (
        <div className="card p-6 text-center">
          <div className="text-2xl mb-2">⏳</div>
          <p className="text-gray-600">Document is being processed. Refresh in a few seconds.</p>
          <button onClick={() => { setLoading(true); api.getDocument(id).then(setDoc).finally(() => setLoading(false)); }} className="mt-3 px-4 py-2 bg-brand-600 text-white rounded-lg text-sm hover:bg-brand-700">
            Refresh
          </button>
        </div>
      )}
    </div>
  );
}
