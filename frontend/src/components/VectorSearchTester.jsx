import React, { useState } from 'react';
import { Search, Database, FileText, Sparkles, Tag, Percent, Loader2 } from 'lucide-react';
import { searchVectorDb } from '../services/api';

export default function VectorSearchTester() {
  const [query, setQuery] = useState('');
  const [topK, setTopK] = useState(3);
  const [searching, setSearching] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setSearching(true);
    setError(null);

    try {
      const data = await searchVectorDb(query.trim(), topK);
      setResults(data);
    } catch (err) {
      console.error('Search error:', err);
      setError(err.message || 'Vector search failed.');
    } finally {
      setSearching(false);
    }
  };

  return (
    <div className="glass-card">
      <div className="glass-page-header border-b border-white/5 pb-4 mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center text-white shadow-[0_4px_16px_rgba(139,92,246,0.2)]">
            <Search size={20} />
          </div>
          <div>
            <h2 className="text-xl font-bold text-gray-100 m-0 leading-tight">Vector Search Tester</h2>
            <p className="text-xs text-gray-400 mt-1">Raw Qdrant Semantic Search (No LLM)</p>
          </div>
        </div>
      </div>

      <form onSubmit={handleSearch} className="flex flex-col sm:flex-row gap-3 mb-8">
        <div className="flex-1 relative group">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter standard query (e.g. 'insulation resistance for pressure cookers')"
            className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3.5 text-sm text-gray-100 placeholder-gray-500 focus:border-purple-500 focus:bg-white/10 transition-all shadow-inner outline-none"
          />
        </div>

        <select
          value={topK}
          onChange={(e) => setTopK(Number(e.target.value))}
          className="bg-white/5 border border-white/10 rounded-xl px-4 py-3.5 text-sm text-gray-100 focus:border-purple-500 outline-none appearance-none min-w-[100px]"
        >
          <option value={3} className="bg-slate-800">Top 3</option>
          <option value={5} className="bg-slate-800">Top 5</option>
          <option value={10} className="bg-slate-800">Top 10</option>
        </select>

        <button
          type="submit"
          disabled={searching || !query.trim()}
          className="flex items-center justify-center gap-2 px-6 py-3.5 rounded-xl font-semibold text-sm transition-all text-white disabled:opacity-50 disabled:cursor-not-allowed bg-gradient-to-r from-purple-500 to-indigo-600 hover:shadow-[0_4px_20px_rgba(139,92,246,0.3)] hover:-translate-y-0.5"
        >
          {searching ? (
            <>
              <Loader2 size={16} className="animate-spin" />
              <span>Searching...</span>
            </>
          ) : (
            <>
              <Search size={16} />
              <span>Search</span>
            </>
          )}
        </button>
      </form>

      {error && (
        <div className="flex items-center gap-3 p-4 mb-6 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
          <div className="shrink-0"><AlertCircle size={18} /></div>
          <div>{error}</div>
        </div>
      )}

      {results && (
        <div className="animate-[fadeIn_0.4s_ease-out]">
          <div className="flex items-center gap-2 mb-4 text-sm font-medium text-purple-400 bg-purple-500/10 border border-purple-500/20 rounded-lg px-4 py-2 w-fit">
            <Sparkles size={16} />
            <span>Found {results.results_count} vectors for "{results.query}"</span>
          </div>

          {results.results_count === 0 ? (
            <div className="flex flex-col items-center justify-center p-12 text-center bg-black/20 border border-white/5 rounded-2xl">
              <Database size={40} className="text-gray-600 mb-3" />
              <p className="text-gray-400 text-sm">No matching vectors found. Ensure you have indexed documents.</p>
            </div>
          ) : (
            <div className="flex flex-col gap-4">
              {results.results.map((res, idx) => (
                <div key={idx} className="bg-white/5 border border-white/10 rounded-2xl p-5 hover:bg-white/[0.07] transition-colors">
                  
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4 pb-4 border-b border-white/10">
                    <div className="flex items-center flex-wrap gap-2">
                      <div className="flex items-center gap-2 bg-blue-500/10 text-blue-400 px-2.5 py-1 rounded-md text-xs font-semibold">
                        <FileText size={14} />
                        {res.document_name}
                      </div>
                      
                      {res.standard_number && res.standard_number !== 'None' && (
                        <div className="bg-orange-500/10 text-orange-400 px-2.5 py-1 rounded-md text-xs font-semibold">
                          {res.standard_number}
                        </div>
                      )}

                      <div className="bg-emerald-500/10 text-emerald-400 px-2.5 py-1 rounded-md text-xs font-semibold">
                        Pg {res.page_number}
                      </div>

                      <div className="bg-purple-500/10 text-purple-400 px-2.5 py-1 rounded-md text-xs font-semibold">
                        {res.section}
                      </div>
                    </div>

                    <div className="flex items-center gap-1.5 text-emerald-400 font-mono text-xs bg-emerald-500/10 px-2 py-1 rounded-md shrink-0">
                      <Percent size={12} />
                      Score: {res.score}
                    </div>
                  </div>

                  <div className="relative">
                    <div className="absolute top-0 left-0 bottom-0 w-1 bg-gradient-to-b from-purple-500 to-blue-500 rounded-full" />
                    <pre className="pl-4 m-0 whitespace-pre-wrap font-sans text-sm text-gray-300 bg-transparent border-none max-h-[250px] overflow-y-auto leading-relaxed">
                      {res.text}
                    </pre>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
