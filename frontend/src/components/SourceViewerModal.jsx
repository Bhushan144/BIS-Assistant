import React, { useState, useEffect } from 'react';
import { X, FileText, ExternalLink, Bookmark, Layers, Eye, Loader2 } from 'lucide-react';
import { fetchSourceDetails, getDocumentFileUrl } from '../services/api';

export default function SourceViewerModal({ source, onClose }) {
  const [details, setDetails] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeView, setActiveView] = useState('snippet'); // 'snippet' | 'pdf'

  useEffect(() => {
    if (!source) return;

    if (source.chunk_id) {
      setLoading(true);
      fetchSourceDetails(source.chunk_id)
        .then((data) => {
          setDetails(data);
        })
        .catch((err) => {
          console.error('Failed to load full source details:', err);
          // Fallback to prop source metadata if endpoint fails
          setDetails({
            chunk_id: source.chunk_id,
            document_id: source.document_id,
            document_name: source.document_name,
            standard_number: source.standard_number,
            page_number: source.page_number,
            section: source.section,
            clause: source.clause,
            text: source.snippet || 'No text snippet available.',
            pdf_url: source.pdf_url || (source.document_id ? getDocumentFileUrl(source.document_id, source.page_number) : '#')
          });
        })
        .finally(() => setLoading(false));
    } else {
      setDetails({
        chunk_id: 'N/A',
        document_id: source.document_id,
        document_name: source.document_name,
        standard_number: source.standard_number,
        page_number: source.page_number,
        section: source.section,
        clause: source.clause,
        text: source.snippet || 'No text snippet available.',
        pdf_url: source.pdf_url || (source.document_id ? getDocumentFileUrl(source.document_id, source.page_number) : '#')
      });
    }
  }, [source]);

  if (!source) return null;

  const pdfViewUrl = details?.document_id
    ? getDocumentFileUrl(details.document_id, details.page_number)
    : source.pdf_url;

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(15, 23, 42, 0.85)',
        backdropFilter: 'blur(4px)',
        zIndex: 1000,
        display: 'flex',
        justifyContent: 'flex-end'
      }}
      onClick={onClose}
    >
      <div
        style={{
          width: '100%',
          maxWidth: '680px',
          height: '100%',
          backgroundColor: '#1E293B',
          borderLeft: '1px solid #334155',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: '-4px 0 25px rgba(0,0,0,0.5)',
          animation: 'slideIn 0.25s ease-out'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div
          style={{
            padding: '1.25rem 1.5rem',
            borderBottom: '1px solid #334155',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: '#0F172A'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <Bookmark style={{ color: '#E05A10' }} size={22} />
            <div>
              <h2 style={{ fontSize: '1.1rem', fontWeight: 600, color: '#F8FAFC' }}>
                Source Citation Reference
              </h2>
              <p style={{ fontSize: '0.8rem', color: '#94A3B8' }}>
                BIS Document Citation & PDF Viewer
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#94A3B8',
              cursor: 'pointer',
              padding: '0.4rem',
              borderRadius: '6px'
            }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Metadata Banner */}
        <div
          style={{
            padding: '1rem 1.5rem',
            background: 'rgba(30, 58, 138, 0.2)',
            borderBottom: '1px solid #334155',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.6rem'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', flexWrap: 'wrap' }}>
            <FileText size={18} style={{ color: '#60A5FA' }} />
            <span style={{ fontWeight: 600, fontSize: '0.95rem', color: '#F8FAFC' }}>
              {details?.document_name || source.document_name}
            </span>

            {(details?.standard_number || source.standard_number) && (
              <span
                style={{
                  background: 'rgba(224, 90, 16, 0.25)',
                  color: '#F97316',
                  border: '1px solid rgba(224, 90, 16, 0.4)',
                  padding: '0.2rem 0.6rem',
                  borderRadius: '4px',
                  fontSize: '0.8rem',
                  fontWeight: 700
                }}
              >
                {details?.standard_number || source.standard_number}
              </span>
            )}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', fontSize: '0.85rem', color: '#CBD5E1' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
              <Layers size={14} style={{ color: '#60A5FA' }} />
              <span>Page {details?.page_number || source.page_number}</span>
            </div>

            <div style={{ color: '#94A3B8' }}>
              Section: <strong style={{ color: '#F8FAFC' }}>{details?.section || source.section}</strong>
            </div>

            {(details?.clause || source.clause) && (
              <div style={{ color: '#94A3B8' }}>
                Clause: <strong style={{ color: '#F8FAFC' }}>{details?.clause || source.clause}</strong>
              </div>
            )}
          </div>
        </div>

        {/* View Mode Toggle */}
        <div
          style={{
            display: 'flex',
            borderBottom: '1px solid #334155',
            background: '#0F172A',
            padding: '0.5rem 1.5rem',
            gap: '0.5rem'
          }}
        >
          <button
            type="button"
            onClick={() => setActiveView('snippet')}
            className={`tab-button ${activeView === 'snippet' ? 'active' : ''}`}
            style={{ padding: '0.4rem 1rem', fontSize: '0.85rem' }}
          >
            <FileText size={15} />
            <span>Retrieved Text Excerpt</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveView('pdf')}
            className={`tab-button ${activeView === 'pdf' ? 'active' : ''}`}
            style={{ padding: '0.4rem 1rem', fontSize: '0.85rem' }}
          >
            <Eye size={15} />
            <span>PDF Page Preview</span>
          </button>

          {pdfViewUrl && (
            <a
              href={pdfViewUrl}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                marginLeft: 'auto',
                display: 'flex',
                alignItems: 'center',
                gap: '0.3rem',
                color: '#60A5FA',
                fontSize: '0.82rem',
                textDecoration: 'none',
                padding: '0.4rem 0.6rem',
                borderRadius: '6px',
                border: '1px solid #334155'
              }}
            >
              <span>Open PDF</span>
              <ExternalLink size={13} />
            </a>
          )}
        </div>

        {/* Content Body */}
        <div style={{ flex: 1, padding: '1.5rem', overflowY: 'auto' }}>
          {loading ? (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '200px', gap: '0.6rem', color: '#94A3B8' }}>
              <Loader2 size={20} className="animate-spin" />
              <span>Loading source citation details...</span>
            </div>
          ) : activeView === 'snippet' ? (
            <div>
              <div style={{ fontSize: '0.85rem', color: '#94A3B8', marginBottom: '0.75rem', fontWeight: 600 }}>
                Exact Text Context Retrieved from Document Chunk:
              </div>
              <pre
                style={{
                  whiteSpace: 'pre-wrap',
                  fontFamily: 'Inter, sans-serif',
                  fontSize: '0.9rem',
                  lineHeight: '1.6',
                  color: '#F8FAFC',
                  background: '#0F172A',
                  padding: '1.25rem',
                  borderRadius: '8px',
                  border: '1px solid #334155'
                }}
              >
                {details?.text || source.snippet || 'No text snippet available for this citation.'}
              </pre>
            </div>
          ) : (
            <div style={{ width: '100%', height: '100%', minHeight: '500px' }}>
              {details?.document_id ? (
                <iframe
                  src={pdfViewUrl}
                  title="PDF Page Viewer"
                  style={{ width: '100%', height: '100%', minHeight: '500px', border: '1px solid #334155', borderRadius: '8px', background: '#fff' }}
                />
              ) : (
                <div className="empty-state">
                  <FileText size={40} />
                  <p>Document ID not available for direct PDF inline viewing.</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
