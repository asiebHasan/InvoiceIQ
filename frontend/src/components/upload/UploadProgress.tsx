'use client';

import { useEffect, useState } from 'react';
import type { Document } from '@/lib/types';
import { statusColor } from '@/lib/utils';

const statusIcon: Record<string, string> = {
  processing: '⏳',
  completed: '✅',
  failed: '❌',
  unknown: '❓',
};

export default function UploadProgress({ documents }: { documents: Document[] }) {
  const [statuses, setStatuses] = useState<Record<string, string>>(
    Object.fromEntries(documents.map((d) => [d.id, d.status]))
  );

  useEffect(() => {
    const interval = setInterval(async () => {
      const pending = Object.entries(statuses).filter(([, s]) => s === 'processing');
      if (pending.length === 0) { clearInterval(interval); return; }

      for (const [id] of pending) {
        try {
          const res = await fetch(`http://localhost:8000/api/documents/${id}`);
          if (res.ok) {
            const doc = await res.json();
            setStatuses((prev) => ({ ...prev, [id]: doc.status }));
          }
        } catch {}
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [statuses]);

  const completed = Object.values(statuses).filter((s) => s === 'completed').length;
  const failed = Object.values(statuses).filter((s) => s === 'failed').length;
  const processing = Object.values(statuses).filter((s) => s === 'processing').length;
  const total = documents.length;

  return (
    <div className="card p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">Upload Results</h2>
        <div className="flex items-center gap-3 text-xs">
          {completed > 0 && <span className="text-green-600">✅ {completed} done</span>}
          {processing > 0 && <span className="text-blue-600">⏳ {processing} processing</span>}
          {failed > 0 && <span className="text-red-600">❌ {failed} failed</span>}
        </div>
      </div>

      <div className="space-y-2">
        {documents.map((doc) => {
          const status = statuses[doc.id] || doc.status;
          return (
            <div key={doc.id} className="flex items-center justify-between p-3 rounded-lg bg-gray-50">
              <div className="flex items-center gap-3 min-w-0">
                <span className="text-lg">{statusIcon[status] || '📄'}</span>
                <div className="min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">{doc.filename}</p>
                  <p className="text-xs text-gray-500">{doc.id.slice(0, 8)}...</p>
                </div>
              </div>
              <div className="flex items-center gap-3 shrink-0">
                <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${statusColor(status)}`}>
                  {status}
                </span>
                {status === 'completed' && (
                  <a href={`/documents/${doc.id}`} className="text-sm text-brand-600 hover:underline">
                    View
                  </a>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {processing === 0 && total > 1 && (
        <div className="mt-4 pt-4 border-t border-gray-200 text-sm text-gray-600">
          {completed} of {total} documents processed successfully
          {failed > 0 && <span className="text-red-600"> · {failed} failed</span>}
        </div>
      )}
    </div>
  );
}
