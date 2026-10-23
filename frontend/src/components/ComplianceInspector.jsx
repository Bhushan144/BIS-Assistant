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
    <div className="glass-card">
      <div className="glass-page-header border-b border-white/5 pb-4 mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center text-white shadow-[0_4px_16px_rgba(245,158,11,0.2)]">
            <ShieldCheck size={20} />
          </div>
          <div>
            <h2 className="text-xl font-bold text-gray-100 m-0 leading-tight">Compliance Inspector</h2>
            <p className="text-xs text-gray-400 mt-1">Automated Testing & Scheme Analysis</p>
          </div>
        </div>
      </div>

      <form onSubmit={handleInspect} className="flex flex-col sm:flex-row gap-3 mb-8">
        <div className="flex-1 relative group">
          <input
            type="text"
            value={productName}
            onChange={(e) => setProductName(e.target.value)}
            placeholder="Enter product name (e.g. 'Food Mixer', 'Pressure Cooker')"
            className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3.5 text-sm text-gray-100 placeholder-gray-500 focus:border-amber-500 focus:bg-white/10 transition-all shadow-inner outline-none"
          />
        </div>
        <button
          type="submit"
          disabled={loading || !productName.trim()}
          className="flex items-center justify-center gap-2 px-6 py-3.5 rounded-xl font-semibold text-sm transition-all text-white disabled:opacity-50 disabled:cursor-not-allowed bg-gradient-to-r from-amber-500 to-orange-600 hover:shadow-[0_4px_20px_rgba(245,158,11,0.3)] hover:-translate-y-0.5"
        >
          {loading ? (
            <>
              <Loader2 size={16} className="animate-spin" />
              <span>Analyzing...</span>
            </>
          ) : (
            <>
              <Search size={16} />
              <span>Inspect</span>
            </>
          )}
        </button>
      </form>

      {error && (
        <div className="flex items-center gap-3 p-4 mb-6 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
          <AlertCircle size={18} />
          <div>{error}</div>
        </div>
      )}

      {report && (
        <div className="flex flex-col gap-6 animate-[fadeIn_0.4s_ease-out]">
          {/* Summary Banner */}
          <div className="relative overflow-hidden rounded-2xl p-6 bg-gradient-to-br from-slate-800 to-slate-900 border border-white/10 shadow-lg">
            {/* Background Glow */}
            <div className="absolute top-0 right-0 -mt-16 -mr-16 w-48 h-48 bg-amber-500/20 blur-3xl rounded-full pointer-events-none" />
            
            <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <div className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-1">
                  Target Product
                </div>
                <h2 className="text-2xl font-bold text-white mb-2">{report.product_name}</h2>
                <div className="flex items-center gap-2 text-sm text-blue-400">
                  <FileText size={16} />
                  <span>{report.document_title}</span>
                </div>
              </div>

              {report.standard_number && (
                <div className="md:text-right flex flex-col md:items-end">
                  <span className="inline-block bg-gradient-to-r from-amber-500 to-orange-600 text-white px-4 py-1.5 rounded-lg text-lg font-bold shadow-md">
                    {report.standard_number}
                  </span>
                  <div className="flex items-center gap-1.5 text-sm text-emerald-400 mt-2 font-medium">
                    <CheckCircle2 size={16} />
                    <span>{report.compliance_status}</span>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Grid Details */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {/* Certification Scheme */}
            <div className="bg-white/5 border border-white/10 rounded-2xl p-5 hover:bg-white/[0.07] transition-colors">
              <div className="flex items-center gap-2 mb-4 text-amber-400 font-semibold">
                <Award size={18} />
                <span>Certification Scheme</span>
              </div>
              <p className="text-sm text-gray-300 leading-relaxed mb-4">
                {report.certification_scheme}
              </p>
              <div className="text-xs text-gray-400 border-t border-white/10 pt-4 mt-auto">
                <strong className="text-gray-300">Marking Rules:</strong> {report.marking_requirements}
              </div>
            </div>

            {/* Mandatory Testing */}
            <div className="bg-white/5 border border-white/10 rounded-2xl p-5 hover:bg-white/[0.07] transition-colors">
              <div className="flex items-center gap-2 mb-4 text-emerald-400 font-semibold">
                <CheckCircle2 size={18} />
                <span>Testing Requirements</span>
              </div>
              <ul className="flex flex-col gap-2.5">
                {report.mandatory_tests.map((test, tIdx) => (
                  <li key={tIdx} className="text-sm text-gray-200 flex items-start gap-2.5">
                    <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 mt-1.5 shrink-0" />
                    <span className="leading-snug">{test}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Documentation Checklist */}
          <div className="bg-white/5 border border-white/10 rounded-2xl p-5 hover:bg-white/[0.07] transition-colors">
            <div className="flex items-center gap-2 mb-5 text-blue-400 font-semibold">
              <ClipboardList size={18} />
              <span>Mandatory Documentation</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {report.required_documents.map((docItem, dIdx) => (
                <div key={dIdx} className="bg-black/20 border border-white/5 p-3 rounded-xl text-sm text-gray-300 flex items-center gap-3">
                  <FileText size={16} className="text-blue-500 shrink-0" />
                  <span className="leading-snug">{docItem}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
