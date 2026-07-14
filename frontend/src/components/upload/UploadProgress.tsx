'use client';

import { useEffect, useState } from 'react';
import type { Document } from '@/lib/types';
import { statusColor } from '@/lib/utils';
import { api } from '@/lib/api';

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
          const doc = await api.getDocument(id);
          setStatuses((prev) => ({ ...prev, [id]: doc.status }));
        } catch {}
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [statuses]);

  return (
    <div className="card p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Upload Results</h2>
      <div className="space-y-3">
        {documents.map((doc) => (
          <div key={doc.id} className="flex items-center justify-between p-3 rounded-lg bg-gray-50">
            <div className="flex items-center gap-3">
              <span className="text-lg">📄</span>
              <span className="text-sm font-medium text-gray-900">{doc.filename}</span>
            </div>
            <div className="flex items-center gap-3">
              <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${statusColor(statuses[doc.id] || doc.status)}`}>
                {statuses[doc.id] || doc.status}
              </span>
              {statuses[doc.id] === 'completed' && (
                <a href={`/documents/${doc.id}`} className="text-sm text-brand-600 hover:underline">
                  View
                </a>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
