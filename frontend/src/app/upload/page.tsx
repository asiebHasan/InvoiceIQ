'use client';

import { useState, useCallback } from 'react';
import { api } from '@/lib/api';
import DropZone from '@/components/upload/DropZone';
import UploadProgress from '@/components/upload/UploadProgress';
import type { Document } from '@/lib/types';

export default function UploadPage() {
  const [uploading, setUploading] = useState(false);
  const [results, setResults] = useState<Document[]>([]);
  const [error, setError] = useState<string | null>(null);

  const handleUpload = useCallback(async (files: File[]) => {
    setUploading(true);
    setError(null);
    try {
      const res = await api.uploadDocuments(files);
      setResults(res);
    } catch (e) {
      setError('Upload failed. Please try again.');
    } finally {
      setUploading(false);
    }
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Upload Documents</h1>
      <DropZone onUpload={handleUpload} disabled={uploading} />
      {error && <div className="card p-4 bg-red-50 border-red-200 text-red-700">{error}</div>}
      {results.length > 0 && <UploadProgress documents={results} />}
    </div>
  );
}
