import React, { useState } from 'react';
import { Search, Database, FileText, Sparkles, Layers, Tag, Percent } from 'lucide-react';
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
    <div className="card-container">
      <div className="card-header">
        <div className="card-title">
          <Search style={{ color: '#3B82F6' }} />
          <span>Phase 3 Vector Store Search Tester (ChromaDB + SentenceTransformers)</span>
        </div>
        <span style={{ fontSize: '0.82rem', color: '#94A3B8' }}>No LLM Generation</span>
      </div>

      <form onSubmit={handleSearch} style={{ display: 'flex', gap: '0.75rem', marginBottom: '1.5rem' }}>
        <div style={{ flex: 1, position: 'relative' }}>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter BIS standard query (e.g., 'What are the insulation resistance tests for pressure cookers?')"
            style={{
              width: '100%',
              background: '#0F172A',
              border: '1px solid #334155',
              borderRadius: '8px',
              padding: '0.75rem 1rem',
              color: '#F8FAFC',
              fontSize: '0.9rem'
            }}
          />
        </div>

        <select
          value={topK}
          onChange={(e) => setTopK(Number(e.target.value))}
          style={{
            background: '#0F172A',
            border: '1px solid #334155',
            borderRadius: '8px',
            padding: '0.75rem 1rem',
            color: '#F8FAFC',
            fontSize: '0.9rem'
          }}
        >
          <option value={3}>Top 3</option>
          <option value={5}>Top 5</option>
          <option value={10}>Top 10</option>
        </select>

        <button
          type="submit"
          className="btn-primary"
          disabled={searching || !query.trim()}
          style={{ padding: '0.75rem 1.5rem' }}
        >
          {searching ? (
            <span>Searching Vectors...</span>
          ) : (
            <>
              <Search size={16} />
              <span>Vector Search</span>
            </>
          )}
        </button>
      </form>

      {error && (
        <div className="alert-box alert-error" style={{ marginBottom: '1.5rem' }}>
          {error}
        </div>
      )}

      {results && (
        <div>
          <div style={{ fontSize: '0.9rem', color: '#94A3B8', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Sparkles size={16} style={{ color: '#F59E0B' }} />
            <span>Retrieved <strong>{results.results_count}</strong> matching vectors for <em>"{results.query}"</em>:</span>
          </div>

          {results.results_count === 0 ? (
            <div className="empty-state">
              <Database size={40} />
              <p>No matching vectors found. Ensure you have indexed at least one processed document in ChromaDB.</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {results.results.map((res, idx) => (
                <div
                  key={idx}
                  style={{
                    background: 'rgba(15, 23, 42, 0.8)',
                    border: '1px solid #334155',
                    borderRadius: '8px',
                    padding: '1.25rem',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.75rem'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid #1E293B', paddingBottom: '0.5rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', flexWrap: 'wrap' }}>
                      <FileText size={16} style={{ color: '#60A5FA' }} />
                      <span style={{ fontWeight: 600, color: '#F8FAFC' }}>{res.document_name}</span>
                      
                      {res.standard_number && res.standard_number !== 'None' && (
                        <span style={{ background: 'rgba(224, 90, 16, 0.2)', color: '#F97316', padding: '0.15rem 0.5rem', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 600 }}>
                          {res.standard_number}
                        </span>
                      )}

                      <span style={{ background: 'rgba(59, 130, 246, 0.15)', color: '#60A5FA', padding: '0.15rem 0.5rem', borderRadius: '4px', fontSize: '0.75rem' }}>
                        Page {res.page_number}
                      </span>

                      <span style={{ background: 'rgba(168, 85, 247, 0.15)', color: '#C084FC', padding: '0.15rem 0.5rem', borderRadius: '4px', fontSize: '0.75rem' }}>
                        Section: {res.section}
                      </span>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.2rem', color: '#34D399', fontWeight: 600, fontSize: '0.85rem' }}>
                      <Percent size={14} />
                      <span>Score: {res.score}</span>
                    </div>
                  </div>

                  <pre style={{
                    whiteSpace: 'pre-wrap',
                    fontFamily: 'Inter, sans-serif',
                    fontSize: '0.88rem',
                    color: '#CBD5E1',
                    background: '#0F172A',
                    padding: '0.85rem',
                    borderRadius: '6px',
                    border: '1px solid #1E293B',
                    maxHeight: '200px',
                    overflowY: 'auto'
                  }}>
                    {res.text}
                  </pre>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
