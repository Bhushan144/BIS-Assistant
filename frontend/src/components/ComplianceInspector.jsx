import React, { useState } from 'react';
import { ShieldCheck, Search, FileText, CheckCircle2, ClipboardList, Award, AlertCircle, Loader2 } from 'lucide-react';
import { checkCompliance } from '../services/api';

export default function ComplianceInspector() {
  const [productName, setProductName] = useState('Food Mixer');
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState(null);
  const [error, setError] = useState(null);

  const handleInspect = async (e) => {
    e.preventDefault();
    if (!productName.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const data = await checkCompliance(productName.trim());
      setReport(data);
    } catch (err) {
      console.error('Compliance inspect error:', err);
      setError(err.message || 'Failed to generate compliance report.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card-container">
      <div className="card-header">
        <div className="card-title">
          <ShieldCheck style={{ color: '#E05A10' }} />
          <span>BIS Product Compliance & Certification Inspector</span>
        </div>
        <span style={{ fontSize: '0.85rem', color: '#94A3B8' }}>Automated Testing & Scheme Analysis</span>
      </div>

      <form onSubmit={handleInspect} style={{ display: 'flex', gap: '0.75rem', marginBottom: '1.5rem' }}>
        <input
          type="text"
          value={productName}
          onChange={(e) => setProductName(e.target.value)}
          placeholder="Enter product name (e.g. 'Food Mixer', 'Pressure Cooker', 'Stainless Steel Bottle')"
          style={{
            flex: 1,
            background: '#0F172A',
            border: '1px solid #334155',
            borderRadius: '8px',
            padding: '0.75rem 1rem',
            color: '#F8FAFC',
            fontSize: '0.9rem'
          }}
        />
        <button
          type="submit"
          className="btn-primary"
          disabled={loading || !productName.trim()}
          style={{ padding: '0.75rem 1.5rem' }}
        >
          {loading ? (
            <>
              <Loader2 size={16} className="animate-spin" />
              <span>Analyzing Standards...</span>
            </>
          ) : (
            <>
              <Search size={16} />
              <span>Inspect Compliance</span>
            </>
          )}
        </button>
      </form>

      {error && (
        <div className="alert-box alert-error" style={{ marginBottom: '1.5rem' }}>
          <AlertCircle size={16} />
          <div>{error}</div>
        </div>
      )}

      {report && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {/* Summary Banner */}
          <div
            style={{
              background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.9), rgba(15, 23, 42, 0.9))',
              border: '1px solid #334155',
              borderRadius: '10px',
              padding: '1.25rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              boxShadow: '0 4px 15px rgba(0,0,0,0.2)'
            }}
          >
            <div>
              <div style={{ fontSize: '0.8rem', color: '#94A3B8', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                Target Product
              </div>
              <h2 style={{ fontSize: '1.3rem', fontWeight: 700, color: '#F8FAFC', margin: '0.2rem 0' }}>
                {report.product_name}
              </h2>
              <div style={{ fontSize: '0.88rem', color: '#60A5FA', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <FileText size={15} />
                <span>{report.document_title}</span>
              </div>
            </div>

            {report.standard_number && (
              <div style={{ textAlign: 'right' }}>
                <span
                  style={{
                    background: 'linear-gradient(135deg, #E05A10, #D97706)',
                    color: '#fff',
                    padding: '0.4rem 0.85rem',
                    borderRadius: '6px',
                    fontSize: '0.95rem',
                    fontWeight: 700,
                    letterSpacing: '0.5px'
                  }}
                >
                  {report.standard_number}
                </span>
                <div style={{ fontSize: '0.78rem', color: '#10B981', marginTop: '0.4rem', fontWeight: 600 }}>
                  ✓ {report.compliance_status}
                </div>
              </div>
            )}
          </div>

          {/* Grid Details */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.25rem' }}>
            {/* Certification Scheme */}
            <div style={{ background: '#0F172A', border: '1px solid #334155', borderRadius: '10px', padding: '1.25rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem', color: '#F59E0B', fontWeight: 600 }}>
                <Award size={18} />
                <span>Applicable Certification Scheme</span>
              </div>
              <p style={{ fontSize: '0.9rem', color: '#CBD5E1', lineHeight: '1.5' }}>
                {report.certification_scheme}
              </p>
              <div style={{ marginTop: '0.85rem', fontSize: '0.82rem', color: '#94A3B8', borderTop: '1px solid #1E293B', paddingTop: '0.6rem' }}>
                <strong>Marking Rules:</strong> {report.marking_requirements}
              </div>
            </div>

            {/* Mandatory Testing Breakdown */}
            <div style={{ background: '#0F172A', border: '1px solid #334155', borderRadius: '10px', padding: '1.25rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem', color: '#34D399', fontWeight: 600 }}>
                <CheckCircle2 size={18} />
                <span>Mandatory Testing Requirements</span>
              </div>
              <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {report.mandatory_tests.map((test, tIdx) => (
                  <li key={tIdx} style={{ fontSize: '0.88rem', color: '#F8FAFC', display: 'flex', alignItems: 'flex-start', gap: '0.5rem' }}>
                    <span style={{ color: '#10B981', fontWeight: 'bold' }}>•</span>
                    <span>{test}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Documentation Checklist */}
          <div style={{ background: '#0F172A', border: '1px solid #334155', borderRadius: '10px', padding: '1.25rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem', color: '#60A5FA', fontWeight: 600 }}>
              <ClipboardList size={18} />
              <span>Mandatory Compliance Document Checklist</span>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '0.75rem' }}>
              {report.required_documents.map((docItem, dIdx) => (
                <div key={dIdx} style={{ background: '#1E293B', padding: '0.65rem 0.85rem', borderRadius: '6px', fontSize: '0.85rem', color: '#CBD5E1', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <FileText size={15} style={{ color: '#60A5FA' }} />
                  <span>{docItem}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
