import React, { useState, useRef } from 'react';
import { UploadCloud, FileText, X, AlertCircle, CheckCircle, Loader2 } from 'lucide-react';
import { uploadPdfs } from '../services/api';

export default function PdfUpload({ onUploadSuccess }) {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState(null);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const validateAndAddFiles = (files) => {
    setMessage(null);
    setError(null);

    const validPdfs = [];
    const invalidNames = [];

    Array.from(files).forEach((file) => {
      if (file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')) {
        validPdfs.push(file);
      } else {
        invalidNames.push(file.name);
      }
    });

    if (invalidNames.length > 0) {
      setError(`Rejected non-PDF file(s): ${invalidNames.join(', ')}`);
    }

    if (validPdfs.length > 0) {
      setSelectedFiles((prev) => {
        const existingNames = new Set(prev.map((f) => f.name));
        const newFiles = validPdfs.filter((f) => !existingNames.has(f.name));
        return [...prev, ...newFiles];
      });
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndAddFiles(e.dataTransfer.files);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndAddFiles(e.target.files);
    }
  };

  const removeFileFromQueue = (index) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const formatFileSize = (bytes) => {
    if (!bytes || isNaN(bytes)) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.max(0, Math.floor(Math.log(bytes) / Math.log(k)));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0) return;

    setUploading(true);
    setMessage(null);
    setError(null);

    try {
      const result = await uploadPdfs(selectedFiles);
      setMessage(result.message || 'Files uploaded successfully!');
      
      if (result.warnings && result.warnings.length > 0) {
        setError(`Warnings: ${result.warnings.join(' | ')}`);
      }

      setSelectedFiles([]);
      if (fileInputRef.current) fileInputRef.current.value = '';

      if (onUploadSuccess) {
        onUploadSuccess();
      }
    } catch (err) {
      console.error(err);
      setError(err.message || 'Failed to upload PDF documents.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="glass-card p-0 overflow-hidden w-full shrink-0">
      <div className="flex items-center justify-between p-5 border-b border-white/10 bg-white/[0.02]">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-blue-500/20 flex items-center justify-center text-blue-400">
            <UploadCloud size={18} />
          </div>
          <span className="font-semibold text-gray-100">Upload BIS Documents</span>
        </div>
        <span className="text-xs font-medium text-gray-500 bg-white/5 px-2 py-1 rounded-md">.pdf only</span>
      </div>

      <div className="p-6">
        <div
          className={`relative flex flex-col items-center justify-center p-10 border-2 border-dashed rounded-2xl cursor-pointer transition-all duration-300 ${
            isDragging 
              ? 'border-blue-500 bg-blue-500/10 scale-[1.01]' 
              : 'border-white/20 bg-white/5 hover:border-white/30 hover:bg-white/10'
          }`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current && fileInputRef.current.click()}
        >
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            multiple
            accept=".pdf,application/pdf"
            className="hidden"
          />
          <UploadCloud size={48} className={`mb-4 transition-colors ${isDragging ? 'text-blue-400' : 'text-gray-500'}`} />
          <h3 className="text-base font-semibold text-gray-200 mb-1">Drag & Drop PDF files</h3>
          <p className="text-sm text-gray-400">or click to browse from computer</p>
        </div>

        {selectedFiles.length > 0 && (
          <div className="mt-6 flex flex-col gap-3 animate-[fadeIn_0.3s_ease-out]">
            <div className="text-sm font-semibold text-gray-400 mb-2">
              Queue ({selectedFiles.length} file{selectedFiles.length > 1 ? 's' : ''}):
            </div>
            
            <div className="flex flex-col gap-2 max-h-[300px] overflow-y-auto pr-2">
              {selectedFiles.map((file, idx) => (
                <div key={idx} className="flex items-center justify-between bg-black/20 border border-white/10 p-3 rounded-xl hover:bg-white/5 transition-colors">
                  <div className="flex items-center gap-3 overflow-hidden">
                    <FileText size={18} className="text-blue-400 shrink-0" />
                    <span className="font-medium text-gray-200 truncate text-sm">{file.name}</span>
                    <span className="text-xs text-gray-500 shrink-0 border-l border-white/10 pl-2">
                      {formatFileSize(file.size)}
                    </span>
                  </div>
                  <button
                    type="button"
                    className="text-gray-500 hover:text-red-400 p-1.5 rounded-lg hover:bg-white/10 transition-colors shrink-0"
                    onClick={() => removeFileFromQueue(idx)}
                    disabled={uploading}
                  >
                    <X size={16} />
                  </button>
                </div>
              ))}
            </div>

            <div className="mt-4 flex justify-end pt-4 border-t border-white/5">
              <button
                type="button"
                className={`flex items-center justify-center gap-2 px-6 py-3 rounded-xl font-semibold text-sm transition-all text-white shadow-lg ${
                  uploading 
                    ? 'bg-blue-600/50 cursor-wait' 
                    : 'bg-gradient-to-r from-blue-600 to-blue-500 hover:shadow-[0_4px_20px_rgba(59,130,246,0.3)] hover:-translate-y-0.5'
                }`}
                onClick={handleUpload}
                disabled={uploading}
              >
                {uploading ? (
                  <>
                    <Loader2 size={16} className="animate-spin" />
                    <span>Uploading & Indexing...</span>
                  </>
                ) : (
                  <>
                    <UploadCloud size={16} />
                    <span>Upload {selectedFiles.length} File{selectedFiles.length > 1 ? 's' : ''}</span>
                  </>
                )}
              </button>
            </div>
          </div>
        )}

        {message && (
          <div className="mt-6 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 px-4 py-3 rounded-xl flex items-center gap-3 text-sm animate-[fadeIn_0.3s_ease-out]">
            <CheckCircle size={18} className="shrink-0" />
            <div>{message}</div>
          </div>
        )}

        {error && (
          <div className="mt-6 bg-red-500/10 border border-red-500/20 text-red-400 px-4 py-3 rounded-xl flex items-center gap-3 text-sm animate-[fadeIn_0.3s_ease-out]">
            <AlertCircle size={18} className="shrink-0" />
            <div>{error}</div>
          </div>
        )}
      </div>
    </div>
  );
}
