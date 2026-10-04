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
    <div className="bg-[#2f2f2f] rounded-2xl border border-white/5 overflow-hidden shadow-sm w-full shrink-0">
      <div className="flex items-center justify-between p-5 border-b border-white/5">
        <div className="flex items-center gap-3">
          <UploadCloud className="text-blue-500" size={20} />
          <span className="font-semibold text-gray-200">Upload Official BIS Documents</span>
        </div>
        <span className="text-xs font-medium text-gray-400">Supports .pdf files only</span>
      </div>

      <div className="p-5">
        {/* Drag and Drop Zone */}
        <div
          className={`relative flex flex-col items-center justify-center p-8 border-2 border-dashed rounded-xl cursor-pointer transition-colors ${
            isDragging ? 'border-blue-500 bg-blue-500/10' : 'border-gray-600 hover:border-gray-500 hover:bg-[#383838]'
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
          <UploadCloud size={40} className={`mb-3 ${isDragging ? 'text-blue-500' : 'text-gray-400'}`} />
          <h3 className="text-base font-semibold text-gray-200 mb-1">Drag & Drop BIS PDF files here</h3>
          <p className="text-sm text-gray-400">or click to browse from your computer (Multiple files allowed)</p>
        </div>

        {/* File Queue Preview */}
        {selectedFiles.length > 0 && (
          <div className="mt-6 flex flex-col gap-3">
            <div className="text-sm font-semibold text-gray-400 mb-1">
              Ready to Upload ({selectedFiles.length} file{selectedFiles.length > 1 ? 's' : ''}):
            </div>
            {selectedFiles.map((file, idx) => (
              <div key={idx} className="flex items-center justify-between bg-[#212121] border border-white/5 p-3 rounded-lg">
                <div className="flex items-center gap-3 overflow-hidden">
                  <FileText size={18} className="text-blue-400 shrink-0" />
                  <span className="font-medium text-gray-200 truncate">{file.name}</span>
                  <span className="text-xs text-gray-500 shrink-0">
                    ({formatFileSize(file.size)})
                  </span>
                </div>
                <button
                  type="button"
                  className="text-gray-400 hover:text-red-400 hover:bg-white/5 p-1.5 rounded-md transition-colors shrink-0"
                  onClick={() => removeFileFromQueue(idx)}
                  disabled={uploading}
                  title="Remove file"
                >
                  <X size={16} />
                </button>
              </div>
            ))}

            <div className="mt-2 flex justify-end">
              <button
                type="button"
                className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-medium text-sm transition-all ${
                  uploading 
                    ? 'bg-blue-600/50 text-white/70 cursor-wait' 
                    : 'bg-blue-600 text-white hover:bg-blue-500'
                }`}
                onClick={handleUpload}
                disabled={uploading}
              >
                {uploading ? (
                  <>
                    <Loader2 size={16} className="animate-spin" />
                    <span>Processing & Indexing...</span>
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

        {/* Success Message Banner */}
        {message && (
          <div className="mt-4 bg-green-900/30 border border-green-500/30 text-green-400 px-4 py-3 rounded-xl flex items-center gap-3 text-sm">
            <CheckCircle size={18} className="shrink-0" />
            <div>{message}</div>
          </div>
        )}

        {/* Error / Warning Alert Banner */}
        {error && (
          <div className="mt-4 bg-red-900/30 border border-red-500/30 text-red-400 px-4 py-3 rounded-xl flex items-center gap-3 text-sm">
            <AlertCircle size={18} className="shrink-0" />
            <div>{error}</div>
          </div>
        )}
      </div>
    </div>
  );
}
