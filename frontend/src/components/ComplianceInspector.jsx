import React, { useState } from 'react';
import { 
  ShieldCheck, 
  Search, 
  FileText, 
  CheckCircle2, 
  ClipboardList, 
  Award, 
  AlertCircle, 
  Loader2, 
  Languages, 
  CheckCheck,
  CheckCircle,
  Scale,
  AlertTriangle,
  FileUp
} from 'lucide-react';
import { checkCompliance } from '../services/api';

export default function ComplianceInspector() {
  const [productName, setProductName] = useState('Pressure Cooker');
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState(null);
  const [error, setError] = useState(null);

  const handleInspect = async (e) => {
    if (e && e.preventDefault) e.preventDefault();
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

  const isNoStandardFound = report && report.compliance_status === 'No Standard Found';

  return (
    <div className="glass-card">
      <div className="glass-page-header border-b border-white/5 pb-4 mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center text-white shadow-[0_4px_16px_rgba(245,158,11,0.2)]">
            <ShieldCheck size={20} />
          </div>
          <div>
            <h2 className="text-xl font-bold text-gray-100 m-0 leading-tight">Compliance Inspector</h2>
            <p className="text-xs text-gray-400 mt-1">Clause-by-Clause Testing & BIS Certification Analysis</p>
          </div>
        </div>
      </div>

      <form onSubmit={handleInspect} className="flex flex-col sm:flex-row gap-3 mb-8">
        <div className="flex-1 relative group">
          <input
            type="text"
            value={productName}
            onChange={(e) => setProductName(e.target.value)}
            placeholder="Enter product name (e.g. 'Pressure Cooker', 'Water Heater', 'Gas Stove', 'IS 2347')"
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
              <span>Auditing Standard...</span>
            </>
          ) : (
            <>
              <Search size={16} />
              <span>Inspect Product</span>
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
          {isNoStandardFound ? (
            /* Dedicated Negative State (Zero Hallucination) */
            <div className="rounded-2xl p-6 bg-slate-900/90 border border-amber-500/25 shadow-xl flex flex-col md:flex-row items-start gap-5">
              <div className="w-12 h-12 rounded-2xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400 shrink-0 mt-1">
                <AlertTriangle size={24} />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-[10px] font-bold text-amber-400 uppercase tracking-widest bg-amber-500/10 px-2.5 py-0.5 rounded-full border border-amber-500/20">
                    STANDARD NOT FOUND IN LIBRARY
                  </span>
                </div>
                <h3 className="text-xl font-bold text-white mb-2">
                  No Matching Indian Standard for "{report.product_name}"
                </h3>
                <p className="text-sm text-gray-300 leading-relaxed mb-4">
                  {report.reason || `No BIS standard covering '${report.product_name}' was found in the indexed library.`}
                </p>

                {report.matched_document && (
                  <div className="text-xs text-gray-400 bg-black/40 p-3 rounded-xl border border-white/5 mb-5 flex items-start gap-2">
                    <AlertCircle size={15} className="text-amber-400 shrink-0 mt-0.5" />
                    <div>
                      <span className="text-gray-200 font-semibold">Closest Document in Library: </span>
                      <span>{report.matched_document}</span>
                      <div className="text-amber-300/80 mt-0.5 italic">
                        Auditor Gate Result: Rejected due to domain mismatch (cannot apply to {report.product_name}).
                      </div>
                    </div>
                  </div>
                )}

                <div className="flex flex-wrap items-center gap-3">
                  <div className="text-xs text-gray-400">
                    To audit compliance for <strong className="text-gray-200">{report.product_name}</strong>, please upload the official standard PDF (e.g. via the Document Library).
                  </div>
                </div>
              </div>
            </div>
          ) : (
            /* Full Audited Compliance Report (Verified Standard Match) */
            <>
              {/* Summary Banner */}
              <div className="relative overflow-hidden rounded-2xl p-6 bg-gradient-to-br from-slate-800 to-slate-900 border border-white/10 shadow-lg">
                <div className="absolute top-0 right-0 -mt-16 -mr-16 w-56 h-56 bg-amber-500/15 blur-3xl rounded-full pointer-events-none" />
                
                <div className="relative z-10 flex flex-col md:flex-row md:items-start justify-between gap-6">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-[10px] font-bold text-amber-400/90 uppercase tracking-widest bg-amber-500/10 px-2.5 py-0.5 rounded-full border border-amber-500/20">
                        TARGET PRODUCT
                      </span>
                      {report.qco_notice && (
                        <span className="text-[10px] font-bold text-rose-400 uppercase tracking-wider bg-rose-500/10 px-2.5 py-0.5 rounded-full border border-rose-500/20">
                          Mandatory QCO
                        </span>
                      )}
                    </div>

                    <h2 className="text-2xl md:text-3xl font-extrabold text-white mb-2 capitalize">
                      {report.product_name}
                    </h2>

                    {/* Official English Title */}
                    <div className="flex items-start gap-2 text-sm text-blue-300 font-medium mb-1">
                      <FileText size={16} className="mt-0.5 shrink-0 text-blue-400" />
                      <span>{report.title_en || report.document_title}</span>
                    </div>

                    {/* Official Hindi Title Translation */}
                    {report.title_hi && (
                      <div className="flex items-center gap-2 text-xs text-amber-200/70 ml-6 font-normal">
                        <Languages size={13} className="text-amber-400/80 shrink-0" />
                        <span>{report.title_hi}</span>
                      </div>
                    )}
                  </div>

                  {/* Standard Badge & Verification */}
                  {report.standard_number && (
                    <div className="md:text-right flex flex-col md:items-end shrink-0">
                      <div className="bg-gradient-to-r from-amber-500 to-orange-600 text-white px-4 py-2 rounded-xl text-xl font-black tracking-wide shadow-lg shadow-amber-500/20">
                        {report.standard_number}
                      </div>
                      <div className="flex items-center gap-1.5 text-xs text-emerald-400 mt-2 font-semibold bg-emerald-500/10 px-2.5 py-1 rounded-lg border border-emerald-500/20">
                        <CheckCircle2 size={14} />
                        <span>{report.compliance_status}</span>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Grid: Scheme & Testing Requirements */}
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
                {/* Certification Scheme & Marking Rules (5 cols) */}
                <div className="lg:col-span-5 flex flex-col gap-5">
                  <div className="bg-white/5 border border-white/10 rounded-2xl p-5 hover:bg-white/[0.07] transition-colors flex-1 flex flex-col">
                    <div className="flex items-center gap-2 mb-3 text-amber-400 font-semibold">
                      <Award size={18} />
                      <span>Certification Scheme</span>
                    </div>
                    <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-sm font-medium text-amber-200 mb-4">
                      {report.certification_scheme}
                    </div>
                    
                    <div className="flex items-center gap-2 mb-2 text-blue-400 font-semibold text-xs uppercase tracking-wider">
                      <Scale size={14} />
                      <span>Marking Rules</span>
                    </div>
                    <p className="text-xs text-gray-300 leading-relaxed bg-black/20 p-3 rounded-xl border border-white/5">
                      {report.marking_requirements}
                    </p>
                    
                    <div className="mt-4 pt-3 border-t border-white/5 flex items-center gap-2 text-[11px] text-gray-400">
                      <CheckCircle size={14} className="text-emerald-400" />
                      <span>Conforms to BIS Act 2016 & Certification Regulations</span>
                    </div>
                  </div>
                </div>

                {/* Testing Requirements (7 cols) */}
                <div className="lg:col-span-7 bg-white/5 border border-white/10 rounded-2xl p-5 hover:bg-white/[0.07] transition-colors">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2 text-emerald-400 font-semibold">
                      <CheckCheck size={18} />
                      <span>Testing Requirements (Clause Breakdown)</span>
                    </div>
                    <span className="text-[11px] text-gray-400 bg-white/5 px-2 py-0.5 rounded-full border border-white/10">
                      {report.mandatory_tests?.length || 0} Verified Tests
                    </span>
                  </div>

                  <div className="flex flex-col gap-3 max-h-[460px] overflow-y-auto pr-1">
                    {report.mandatory_tests && report.mandatory_tests.length > 0 ? (
                      report.mandatory_tests.map((test, tIdx) => {
                        const isObj = typeof test === 'object' && test !== null;
                        const clause = isObj ? test.clause : null;
                        const testName = isObj ? (test.test_name || test.name) : test;
                        const testType = isObj ? test.test_type : null;
                        const req = isObj ? (test.requirement || test.description) : null;

                        return (
                          <div 
                            key={tIdx} 
                            className="p-3.5 rounded-xl bg-black/30 border border-white/5 hover:border-emerald-500/30 transition-all flex flex-col gap-1.5"
                          >
                            <div className="flex items-start justify-between gap-2">
                              <div className="flex flex-wrap items-center gap-2">
                                {clause && (
                                  <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
                                    {clause}
                                  </span>
                                )}
                                <span className="text-sm font-semibold text-gray-100">
                                  {testName}
                                </span>
                              </div>
                              {testType && (
                                <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-white/5 text-gray-300 border border-white/10 shrink-0">
                                  {testType}
                                </span>
                              )}
                            </div>
                            {req && (
                              <p className="text-xs text-gray-300 leading-relaxed m-0">
                                {req}
                              </p>
                            )}
                          </div>
                        );
                      })
                    ) : (
                      <div className="text-xs text-gray-400 p-4 text-center">
                        No specific tests indexed for this document. Refer to full standard.
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Documentation Checklist (Scheme-I & SIT Guidelines) */}
              <div className="bg-white/5 border border-white/10 rounded-2xl p-5 hover:bg-white/[0.07] transition-colors">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
                  <div className="flex items-center gap-2 text-blue-400 font-semibold">
                    <ClipboardList size={18} />
                    <span>Documentation Checklist (Scheme-I & SIT Guidelines)</span>
                  </div>
                  <span className="text-[11px] text-gray-400">
                    Mandatory Factory & Quality Assurance Records
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
                  {report.required_documents && report.required_documents.map((docItem, dIdx) => {
                    const isObj = typeof docItem === 'object' && docItem !== null;
                    const docTitle = isObj ? (docItem.document || docItem.name || docItem.title) : docItem;
                    const category = isObj ? docItem.category : null;
                    const desc = isObj ? docItem.description : null;

                    return (
                      <div 
                        key={dIdx} 
                        className="bg-black/30 border border-white/5 p-3.5 rounded-xl flex flex-col justify-between gap-2 hover:border-blue-500/30 transition-all"
                      >
                        <div className="flex items-start gap-2.5">
                          <FileText size={17} className="text-blue-400 shrink-0 mt-0.5" />
                          <div>
                            <div className="text-sm font-semibold text-gray-200">
                              {docTitle}
                            </div>
                            {desc && (
                              <div className="text-xs text-gray-400 mt-1 leading-snug">
                                {desc}
                              </div>
                            )}
                          </div>
                        </div>
                        {category && (
                          <div className="self-start text-[10px] font-medium px-2 py-0.5 rounded bg-blue-500/10 text-blue-300 border border-blue-500/20 ml-7">
                            {category}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
