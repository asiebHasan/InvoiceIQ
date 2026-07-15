'use client';

import { useCallback, useState, useRef } from 'react';

interface Props {
  onUpload: (files: File[]) => void;
  disabled: boolean;
}

export default function DropZone({ onUpload, disabled }: Props) {
  const [dragging, setDragging] = useState(false);
  const [selected, setSelected] = useState<File[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);

  const acceptFiles = (fileList: FileList | File[]) => {
    const files = Array.from(fileList).filter((f) => f.name.toLowerCase().endsWith('.pdf'));
    if (files.length) setSelected((prev) => [...prev, ...files]);
  };

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      acceptFiles(e.dataTransfer.files);
    },
    []
  );

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files) acceptFiles(e.target.files);
      e.target.value = '';
    },
    []
  );

  const removeFile = (index: number) => {
    setSelected((prev) => prev.filter((_, i) => i !== index));
  };

  const clearAll = () => setSelected([]);

  const handleSubmit = () => {
    if (selected.length) {
      onUpload(selected);
      setSelected([]);
    }
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1048576).toFixed(1)} MB`;
  };

  return (
    <div className="space-y-4">
      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        className={`card p-12 text-center border-2 border-dashed transition-colors cursor-pointer ${
          dragging ? 'border-brand-500 bg-brand-50' : 'border-gray-300 hover:border-gray-400'
        } ${disabled ? 'opacity-50 pointer-events-none' : ''}`}
      >
        <input
          ref={inputRef}
          id="file-upload"
          type="file"
          accept=".pdf"
          multiple
          onChange={handleChange}
          className="hidden"
          disabled={disabled}
        />
        <label htmlFor="file-upload" className="cursor-pointer">
          <div className="text-4xl mb-3">📤</div>
          <p className="text-lg font-medium text-gray-700">Drop PDF files here or click to browse</p>
          <p className="text-sm text-gray-500 mt-1">Supports invoices, receipts, purchase orders, bank statements</p>
          <p className="text-xs text-gray-400 mt-2">Multiple files supported</p>
        </label>
      </div>

      {selected.length > 0 && (
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-gray-900">
              {selected.length} file{selected.length !== 1 ? 's' : ''} selected
              <span className="text-gray-400 font-normal ml-2">
                ({formatSize(selected.reduce((sum, f) => sum + f.size, 0))} total)
              </span>
            </h3>
            <button
              onClick={clearAll}
              className="text-xs text-gray-500 hover:text-red-600"
            >
              Clear all
            </button>
          </div>
          <div className="space-y-2 max-h-48 overflow-y-auto mb-4">
            {selected.map((file, i) => (
              <div key={`${file.name}-${i}`} className="flex items-center justify-between p-2 rounded bg-gray-50 text-sm">
                <div className="flex items-center gap-2 min-w-0">
                  <span>📄</span>
                  <span className="truncate text-gray-700">{file.name}</span>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <span className="text-gray-400 text-xs">{formatSize(file.size)}</span>
                  <button
                    onClick={() => removeFile(i)}
                    className="text-gray-400 hover:text-red-500 text-xs"
                  >
                    ✕
                  </button>
                </div>
              </div>
            ))}
          </div>
          <button
            onClick={handleSubmit}
            disabled={disabled}
            className="w-full px-4 py-2.5 bg-brand-600 text-white rounded-lg text-sm font-medium hover:bg-brand-700 disabled:opacity-50"
          >
            {disabled ? 'Uploading...' : `Upload ${selected.length} file${selected.length !== 1 ? 's' : ''}`}
          </button>
        </div>
      )}
    </div>
  );
}
