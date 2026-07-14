'use client';

import { useCallback, useState } from 'react';

interface Props {
  onUpload: (files: File[]) => void;
  disabled: boolean;
}

export default function DropZone({ onUpload, disabled }: Props) {
  const [dragging, setDragging] = useState(false);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      const files = Array.from(e.dataTransfer.files).filter((f) => f.name.endsWith('.pdf'));
      if (files.length) onUpload(files);
    },
    [onUpload]
  );

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = Array.from(e.target.files || []).filter((f) => f.name.endsWith('.pdf'));
      if (files.length) onUpload(files);
    },
    [onUpload]
  );

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      className={`card p-12 text-center border-2 border-dashed transition-colors cursor-pointer ${
        dragging ? 'border-brand-500 bg-brand-50' : 'border-gray-300 hover:border-gray-400'
      } ${disabled ? 'opacity-50 pointer-events-none' : ''}`}
    >
      <input
        type="file"
        accept=".pdf"
        multiple
        onChange={handleChange}
        className="hidden"
        id="file-upload"
        disabled={disabled}
      />
      <label htmlFor="file-upload" className="cursor-pointer">
        <div className="text-4xl mb-3">📤</div>
        <p className="text-lg font-medium text-gray-700">Drop PDF files here or click to browse</p>
        <p className="text-sm text-gray-500 mt-1">Supports invoices, receipts, purchase orders, bank statements</p>
      </label>
    </div>
  );
}
