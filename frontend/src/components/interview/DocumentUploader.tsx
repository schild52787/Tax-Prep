import { useState, useCallback } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../api/client';
import { Upload, FileText, Check, AlertCircle } from 'lucide-react';

interface Props {
  returnId: string;
}

interface ExtractedData {
  document_type: string;
  extracted_data: Record<string, string | number>;
  confidence: string;
  raw_text_preview: string;
}

const DOC_TYPE_LABELS: Record<string, string> = {
  w2: 'W-2 (Wage and Tax Statement)',
  '1099_int': '1099-INT (Interest Income)',
  '1099_div': '1099-DIV (Dividends)',
  '1099_b': '1099-B (Broker Proceeds)',
  '1099_r': '1099-R (Retirement Distributions)',
  unknown: 'Unknown Document',
};

export function DocumentUploader({ returnId }: Props) {
  const [dragActive, setDragActive] = useState(false);
  const [extracted, setExtracted] = useState<ExtractedData | null>(null);
  const [imported, setImported] = useState(false);
  const queryClient = useQueryClient();

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      const { data } = await api.post(
        `/returns/${returnId}/documents/upload`,
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      );
      return data as ExtractedData;
    },
    onSuccess: (data) => {
      setExtracted(data);
      setImported(false);
    },
  });

  const importMutation = useMutation({
    mutationFn: async () => {
      if (!extracted) return;
      await api.post(`/returns/${returnId}/documents/import`, {
        document_type: extracted.document_type,
        data: extracted.extracted_data,
      });
    },
    onSuccess: () => {
      setImported(true);
      queryClient.invalidateQueries({ queryKey: ['w2s', returnId] });
      queryClient.invalidateQueries({ queryKey: ['interest1099s', returnId] });
      queryClient.invalidateQueries({ queryKey: ['dividend1099s', returnId] });
    },
  });

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragActive(false);
      const file = e.dataTransfer.files[0];
      if (file && file.type === 'application/pdf') {
        uploadMutation.mutate(file);
      }
    },
    [uploadMutation]
  );

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) uploadMutation.mutate(file);
    },
    [uploadMutation]
  );

  return (
    <div className="space-y-4">
      <h3 className="font-semibold text-gray-700">Upload Tax Documents</h3>
      <p className="text-xs text-gray-500">
        Upload PDF copies of your W-2s and 1099s. We'll automatically extract the data for you to review.
      </p>

      {/* Drop zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
        onDragLeave={() => setDragActive(false)}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          dragActive
            ? 'border-accent bg-accent/5'
            : 'border-border hover:border-accent/30'
        }`}
      >
        <Upload className="w-8 h-8 text-gray-400 mx-auto mb-2" />
        <p className="text-sm text-gray-600">
          Drag and drop a PDF here, or{' '}
          <label className="text-accent cursor-pointer hover:underline">
            browse
            <input
              type="file"
              accept=".pdf"
              onChange={handleFileSelect}
              className="hidden"
            />
          </label>
        </p>
        <p className="text-xs text-gray-400 mt-1">Supports W-2, 1099-INT, 1099-DIV, 1099-B, 1099-R</p>
      </div>

      {uploadMutation.isPending && (
        <div className="bg-blue-50 rounded-lg p-4 text-sm text-blue-700">
          Processing document...
        </div>
      )}

      {uploadMutation.isError && (
        <div className="bg-red-50 rounded-lg p-4 text-sm text-red-700 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          Failed to process document. Make sure it's a valid PDF.
        </div>
      )}

      {/* Extracted data review */}
      {extracted && !imported && (
        <div className="bg-white border border-border rounded-lg p-4">
          <div className="flex items-center gap-2 mb-3">
            <FileText className="w-5 h-5 text-accent" />
            <h4 className="font-medium text-gray-800">
              Detected: {DOC_TYPE_LABELS[extracted.document_type] || extracted.document_type}
            </h4>
            <span className="text-xs bg-gray-100 px-2 py-0.5 rounded text-gray-500">
              {extracted.confidence} confidence
            </span>
          </div>

          <div className="space-y-1 mb-4">
            {Object.entries(extracted.extracted_data).map(([key, value]) => (
              <div key={key} className="flex justify-between text-sm">
                <span className="text-gray-600">{key.replace(/_/g, ' ')}</span>
                <span className="font-medium">{typeof value === 'number' ? `$${value.toLocaleString()}` : value}</span>
              </div>
            ))}
          </div>

          <div className="flex gap-2">
            <button
              onClick={() => importMutation.mutate()}
              disabled={importMutation.isPending}
              className="bg-success text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-success/90 disabled:opacity-50 transition-colors"
            >
              {importMutation.isPending ? 'Importing...' : 'Import Data'}
            </button>
            <button
              onClick={() => setExtracted(null)}
              className="px-4 py-2 rounded-lg text-sm text-gray-600 hover:bg-gray-100 transition-colors"
            >
              Discard
            </button>
          </div>
        </div>
      )}

      {imported && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-center gap-2 text-sm text-green-700">
          <Check className="w-4 h-4" />
          Document data imported successfully!
        </div>
      )}
    </div>
  );
}
