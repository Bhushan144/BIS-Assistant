import React, { useState } from 'react';
import { Database, FileText, RefreshCw, Layers, Cpu, CheckCircle, AlertCircle, Loader2, Trash2 } from 'lucide-react';
import { processDocument, indexDocument, wipeDocuments, deleteDocument } from '../services/api';

export default function DocumentList({ documents, loading, onRefresh }) {
  const [actionId, setActionId] = useState(null);
  const [actionType, setActionType] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);

  const formatFileSize = (bytes) => {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const handleWipe = async () => {
    if (!window.confirm("Are you sure you want to delete ALL documents? This cannot be undone.")) return;
    
    setActionId('wipe');
    setActionType('wipe');
    setErrorMessage(null);
    try {
      await wipeDocuments();
      if (onRefresh) onRefresh();
    } catch (err) {
      console.error('Failed to wipe documents:', err);
      setErrorMessage(err.message || 'Error wiping documents');
    } finally {
      setActionId(null);
      setActionType(null);
    }
  };

  const handleDelete = async (documentId) => {
    if (!window.confirm("Are you sure you want to delete this document?")) return;
    
    setActionId(documentId);
    setActionType('delete');
    setErrorMessage(null);
    try {
      await deleteDocument(documentId);
      if (onRefresh) onRefresh();
    } catch (err) {
      console.error('Failed to delete document:', err);
      setErrorMessage(err.message || 'Error deleting document');
    } finally {
      setActionId(null);
      setActionType(null);
    }
  };

  const handleProcess = async (documentId) => {
    setActionId(documentId);
    setActionType('process');
    setErrorMessage(null);
    try {
      await processDocument(documentId);
      if (onRefresh) onRefresh();
    } catch (err) {
      console.error('Failed to process document:', err);
      setErrorMessage(err.message || 'Error processing document');
    } finally {
      setActionId(null);
      setActionType(null);
    }
  };

  const handleIndex = async (documentId) => {
    setActionId(documentId);
    setActionType('index');
    setErrorMessage(null);
    try {
      await indexDocument(documentId);
      if (onRefresh) onRefresh();
    } catch (err) {
      console.error('Failed to index document:', err);
      setErrorMessage(err.message || 'Error indexing document in Qdrant');
    } finally {
      setActionId(null);
      setActionType(null);
    }
  };

  const renderStatusBadge = (doc) => {
    const status = doc.status || 'uploaded';
    
    if (status === 'indexed') {
      return (
        <span className="inline-flex items-center px-2.5 py-1 rounded-md text-[11px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          Indexed ({doc.indexed_chunk_count || doc.chunk_count || 0} vectors)
        </span>
      );
    }
    if (status === 'indexing' || (actionId === doc.document_id && actionType === 'index')) {
      return (
        <span className="inline-flex items-center px-2.5 py-1 rounded-md text-[11px] font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/20">
          Indexing...
        </span>
      );
    }
    if (status === 'processed') {
      return (
        <span className="inline-flex items-center px-2.5 py-1 rounded-md text-[11px] font-semibold bg-purple-500/10 text-purple-400 border border-purple-500/20">
          Processed ({doc.chunk_count || 0} chunks)
        </span>
      );
    }
    if (status === 'processing' || (actionId === doc.document_id && actionType === 'process')) {
      return (
        <span className="inline-flex items-center px-2.5 py-1 rounded-md text-[11px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
          Processing...
        </span>
      );
    }
    if (status === 'error') {
      return (
        <span className="inline-flex items-center px-2.5 py-1 rounded-md text-[11px] font-semibold bg-red-500/10 text-red-400 border border-red-500/20">
          Error
        </span>
      );
    }
    return (
      <span className="inline-flex items-center px-2.5 py-1 rounded-md text-[11px] font-semibold bg-white/10 text-gray-300 border border-white/10">
        Uploaded
      </span>
    );
  };

  const renderActionButton = (doc) => {
    const isBusy = actionId === doc.document_id;
    const status = doc.status || 'uploaded';

    if (status === 'uploaded' || status === 'processing') {
      return (
        <button
          type="button"
          onClick={() => handleProcess(doc.document_id)}
          disabled={isBusy}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-bold uppercase tracking-wide transition-all ${
            isBusy ? 'bg-white/5 text-gray-500 cursor-not-allowed' : 'bg-blue-500/20 text-blue-400 hover:bg-blue-500/30'
          }`}
        >
          {isBusy && actionType === 'process' ? (
            <>
              <Loader2 size={12} className="animate-spin" />
              <span>Wait...</span>
            </>
          ) : (
            <>
              <Cpu size={12} />
              <span>Process</span>
            </>
          )}
        </button>
      );
    }

    if (status === 'processed' || status === 'indexing') {
      return (
        <button
          type="button"
          onClick={() => handleIndex(doc.document_id)}
          disabled={isBusy}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-bold uppercase tracking-wide transition-all ${
            isBusy ? 'bg-white/5 text-gray-500 cursor-not-allowed' : 'bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30'
          }`}
        >
          {isBusy && actionType === 'index' ? (
            <>
              <Loader2 size={12} className="animate-spin" />
              <span>Wait...</span>
            </>
          ) : (
            <>
              <Database size={12} />
              <span>Index</span>
            </>
          )}
        </button>
      );
    }

    if (status === 'indexed') {
      return (
        <div className="flex items-center gap-2">
          <span className="flex items-center gap-1 text-[11px] text-emerald-400 font-bold bg-emerald-500/10 px-2 py-1 rounded-md">
            <CheckCircle size={12} /> Ready
          </span>
          <button
            type="button"
            onClick={() => handleIndex(doc.document_id)}
            disabled={isBusy}
            className="text-[10px] uppercase font-bold text-gray-400 hover:text-white bg-white/5 hover:bg-white/10 px-2 py-1.5 rounded-md transition-colors disabled:opacity-50"
            title="Re-index vectors in Qdrant"
          >
            Re-index
          </button>
        </div>
      );
    }

    return (
      <button
        type="button"
        onClick={() => handleProcess(doc.document_id)}
        className="bg-red-500/20 text-red-400 hover:bg-red-500/30 px-3 py-1.5 rounded-lg text-[11px] font-bold uppercase tracking-wide transition-colors"
      >
        Retry
      </button>
    );
  };

  return (
    <div className="glass-card p-0 overflow-hidden w-full shrink-0">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between p-5 border-b border-white/10 bg-white/[0.02] gap-4">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-orange-500/20 flex items-center justify-center text-orange-400">
            <Database size={18} />
          </div>
          <div className="flex flex-col">
            <span className="font-semibold text-gray-100">Document Registry</span>
            <span className="text-xs font-medium text-gray-500">{documents.length} File{documents.length !== 1 ? 's' : ''} in store</span>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <button
            onClick={handleWipe}
            disabled={loading || actionId !== null || documents.length === 0}
            className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-red-400 bg-red-500/10 hover:bg-red-500/20 px-3 py-2 rounded-lg transition-colors disabled:opacity-50"
          >
            <Trash2 size={14} className={actionType === 'wipe' ? 'animate-pulse' : ''} />
            <span className="hidden sm:inline">Wipe All</span>
          </button>
          <button
            onClick={onRefresh}
            disabled={loading || actionId !== null}
            className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-gray-300 bg-white/5 hover:bg-white/10 px-3 py-2 rounded-lg transition-colors disabled:opacity-50"
          >
            <RefreshCw size={14} className={loading && actionType !== 'wipe' ? 'animate-spin' : ''} />
            <span className="hidden sm:inline">Refresh</span>
          </button>
        </div>
      </div>

      <div className="p-0">
        {errorMessage && (
          <div className="m-5 bg-red-500/10 border border-red-500/20 text-red-400 px-4 py-3 rounded-xl flex items-center gap-3 text-sm animate-[fadeIn_0.3s_ease-out]">
            <AlertCircle size={18} className="shrink-0" />
            <div>{errorMessage}</div>
          </div>
        )}

        {documents.length === 0 ? (
          <div className="flex flex-col items-center justify-center p-12 text-center">
            <div className="w-16 h-16 rounded-2xl bg-white/5 flex items-center justify-center mb-4">
              <FileText size={32} className="text-gray-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-300 mb-2">No Documents Yet</h3>
            <p className="text-sm text-gray-500 max-w-sm">Upload BIS standards to populate your AI knowledge base.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse whitespace-nowrap">
              <thead>
                <tr className="bg-white/5 border-b border-white/10">
                  <th className="px-5 py-3 text-[10px] font-bold text-gray-400 uppercase tracking-wider">Document</th>
                  <th className="px-5 py-3 text-[10px] font-bold text-gray-400 uppercase tracking-wider">Standard</th>
                  <th className="px-5 py-3 text-[10px] font-bold text-gray-400 uppercase tracking-wider">Details</th>
                  <th className="px-5 py-3 text-[10px] font-bold text-gray-400 uppercase tracking-wider">Status</th>
                  <th className="px-5 py-3 text-[10px] font-bold text-gray-400 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {documents.map((doc) => (
                  <tr key={doc.document_id} className="hover:bg-white/[0.03] transition-colors">
                    <td className="px-5 py-4">
                      <div className="flex items-center gap-3">
                        <FileText size={16} className="text-blue-400 shrink-0" />
                        <span className="font-medium text-gray-200 text-sm">{doc.filename}</span>
                      </div>
                    </td>
                    <td className="px-5 py-4">
                      {doc.standard_number ? (
                        <span className="inline-flex items-center px-2 py-1 rounded-md text-[11px] font-bold bg-orange-500/10 text-orange-500 border border-orange-500/20">
                          {doc.standard_number}
                        </span>
                      ) : (
                        <span className="text-xs text-gray-500">
                          {doc.document_title ? doc.document_title.slice(0, 30) + '...' : 'Unknown'}
                        </span>
                      )}
                    </td>
                    <td className="px-5 py-4 text-xs text-gray-400">
                      <div className="flex flex-col gap-1">
                        <span className="flex items-center gap-1.5">
                          <Layers size={12} className="text-gray-500" />
                          {doc.page_count} pages
                        </span>
                        <span>{formatFileSize(doc.file_size)}</span>
                      </div>
                    </td>
                    <td className="px-5 py-4">
                      {renderStatusBadge(doc)}
                    </td>
                    <td className="px-5 py-4">
                      <div className="flex items-center gap-3">
                        {renderActionButton(doc)}
                        <button
                          type="button"
                          onClick={() => handleDelete(doc.document_id)}
                          disabled={actionId === doc.document_id}
                          className="text-gray-500 hover:text-red-400 bg-white/5 hover:bg-white/10 p-2 rounded-lg transition-colors disabled:opacity-50"
                          title="Delete document"
                        >
                          <Trash2 size={14} className={actionId === doc.document_id && actionType === 'delete' ? 'animate-pulse text-red-500' : ''} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
