const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...options?.headers },
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export const api = {
  // Documents
  listDocuments: (params?: Record<string, string>) => {
    const qs = params ? '?' + new URLSearchParams(params).toString() : '';
    return request<import('./types').DocumentListResponse>(`/api/documents${qs}`);
  },
  getDocument: (id: string) =>
    request<import('./types').DocumentDetail>(`/api/documents/${id}`),
  deleteDocument: (id: string) =>
    request<{ message: string }>(`/api/documents/${id}`, { method: 'DELETE' }),
  reprocessDocument: (id: string) =>
    request<any>(`/api/documents/${id}/reprocess`, { method: 'POST' }),
  resolveAnomaly: (docId: string, anomalyId: string, isResolved: boolean) =>
    request<import('./types').Anomaly>(`/api/documents/${docId}/anomalies/${anomalyId}`, {
      method: 'PATCH',
      body: JSON.stringify({ is_resolved: isResolved }),
    }),

  // Upload
  uploadDocuments: async (files: File[]) => {
    const formData = new FormData();
    files.forEach((f) => formData.append('files', f));
    const res = await fetch(`${API_BASE}/api/documents/upload`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
    return res.json();
  },

  // Dashboard
  getStats: () => request<import('./types').DashboardStats>('/api/dashboard/stats'),
  getRecent: () => request<{ documents: import('./types').Document[] }>('/api/dashboard/recent'),
  getTimeline: (days?: number) =>
    request<{ timeline: import('./types').TimelinePoint[] }>(
      `/api/dashboard/timeline${days ? `?days=${days}` : ''}`
    ),

  // Export
  exportCsv: (params?: Record<string, string>) => {
    const qs = params ? '?' + new URLSearchParams(params).toString() : '';
    return `${API_BASE}/api/export/csv${qs}`;
  },
  exportExcel: (params?: Record<string, string>) => {
    const qs = params ? '?' + new URLSearchParams(params).toString() : '';
    return `${API_BASE}/api/export/excel${qs}`;
  },

  // Health
  getHealth: () => request<Record<string, string>>('/api/health/services'),

  // Chat
  chat: (message: string, documentId?: string) =>
    request<import('./types').ChatResponse>('/api/chat', {
      method: 'POST',
      body: JSON.stringify({ message, document_id: documentId || null }),
    }),
};
