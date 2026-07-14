import Link from 'next/link';
import type { Document } from '@/lib/types';
import { formatDate, formatFileSize, documentTypeColor, statusColor } from '@/lib/utils';

export default function RecentDocuments({ documents }: { documents: Document[] }) {
  return (
    <div className="card p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Documents</h2>
      {documents.length === 0 ? (
        <p className="text-sm text-gray-400">No documents uploaded yet</p>
      ) : (
        <div className="space-y-3">
          {documents.map((doc) => (
            <Link
              key={doc.id}
              href={`/documents/${doc.id}`}
              className="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-center gap-3 min-w-0">
                <span className="text-lg">📄</span>
                <div className="min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">{doc.filename}</p>
                  <p className="text-xs text-gray-500">{formatDate(doc.created_at)}</p>
                </div>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${documentTypeColor(doc.document_type)}`}>
                  {doc.document_type}
                </span>
                <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${statusColor(doc.status)}`}>
                  {doc.status}
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
