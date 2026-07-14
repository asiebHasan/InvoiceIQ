import Link from 'next/link';
import type { Document } from '@/lib/types';
import { formatDate, formatFileSize, formatCurrency, documentTypeColor, statusColor } from '@/lib/utils';

export default function DocumentTable({ documents }: { documents: Document[] }) {
  if (documents.length === 0) {
    return <div className="card p-12 text-center text-gray-500">No documents to display</div>;
  }

  return (
    <div className="card overflow-hidden">
      <table className="w-full">
        <thead className="bg-gray-50 border-b border-gray-200">
          <tr>
            <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Filename</th>
            <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Type</th>
            <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Date</th>
            <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Status</th>
            <th className="text-right px-4 py-3 text-xs font-medium text-gray-500 uppercase">Amount</th>
            <th className="text-center px-4 py-3 text-xs font-medium text-gray-500 uppercase">Anomalies</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {documents.map((doc) => (
            <tr key={doc.id} className="hover:bg-gray-50 transition-colors">
              <td className="px-4 py-3">
                <Link href={`/documents/${doc.id}`} className="text-sm font-medium text-brand-600 hover:underline">
                  {doc.filename}
                </Link>
              </td>
              <td className="px-4 py-3">
                <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${documentTypeColor(doc.document_type)}`}>
                  {doc.document_type}
                </span>
              </td>
              <td className="px-4 py-3 text-sm text-gray-600">{formatDate(doc.created_at)}</td>
              <td className="px-4 py-3">
                <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${statusColor(doc.status)}`}>
                  {doc.status}
                </span>
              </td>
              <td className="px-4 py-3 text-sm text-gray-900 text-right">{formatCurrency(doc.total_amount)}</td>
              <td className="px-4 py-3 text-center">
                {doc.anomaly_count > 0 ? (
                  <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                    {doc.anomaly_count}
                  </span>
                ) : (
                  <span className="text-xs text-gray-400">-</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
