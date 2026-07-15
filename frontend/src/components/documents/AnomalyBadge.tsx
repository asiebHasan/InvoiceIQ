'use client';

import { useState } from 'react';
import type { Anomaly } from '@/lib/types';
import { anomalySeverityColor } from '@/lib/utils';
import { api } from '@/lib/api';

interface Props {
  anomaly: Anomaly;
  documentId: string;
  onResolve?: (anomaly: Anomaly) => void;
}

export default function AnomalyBadge({ anomaly, documentId, onResolve }: Props) {
  const [resolved, setResolved] = useState(anomaly.is_resolved);
  const [loading, setLoading] = useState(false);

  const handleToggle = async () => {
    setLoading(true);
    try {
      const updated = await api.resolveAnomaly(documentId, anomaly.id, !resolved);
      setResolved(updated.is_resolved);
      onResolve?.(updated);
    } catch {}
    setLoading(false);
  };

  return (
    <div className={`flex items-start gap-3 p-3 rounded-lg border ${
      resolved ? 'bg-gray-50 border-gray-200 opacity-60' : anomalySeverityColor(anomaly.severity)
    }`}>
      <span className="text-lg shrink-0">
        {resolved ? '✓' : anomaly.severity === 'critical' ? '🔴' : anomaly.severity === 'high' ? '🟠' : anomaly.severity === 'medium' ? '🟡' : '🔵'}
      </span>
      <div className="flex-1 min-w-0">
        <p className={`text-sm font-medium ${resolved ? 'line-through text-gray-500' : ''}`}>{anomaly.description}</p>
        <p className="text-xs opacity-75 mt-0.5">{anomaly.anomaly_type.replace(/_/g, ' ')}</p>
      </div>
      <button
        onClick={handleToggle}
        disabled={loading}
        className={`shrink-0 px-2.5 py-1 rounded text-xs font-medium transition-colors ${
          resolved
            ? 'text-gray-600 hover:text-gray-900 hover:bg-gray-200'
            : 'text-brand-700 hover:bg-brand-100'
        } disabled:opacity-50`}
      >
        {loading ? '...' : resolved ? 'Undo' : 'Resolve'}
      </button>
    </div>
  );
}
