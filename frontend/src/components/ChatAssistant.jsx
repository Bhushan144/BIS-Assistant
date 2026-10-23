import React, { useState, useRef, useEffect } from 'react';
import { ShieldCheck, Send, Bot, Bookmark, Loader2, AlertCircle } from 'lucide-react';
import { queryRag } from '../services/api';
import SourceViewerModal from './SourceViewerModal';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export default function ChatAssistant({ language = 'English' }) {
  const [messages, setMessages] = useState([
    {
      sender: 'assistant',
      text: 'Hello! I am your AI-Powered BIS Standards Assistant. Ask me any question regarding official Bureau of Indian Standards (BIS).',
      sources: []
    }
  ]);
  const [inputQuery, setInputQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedSource, setSelectedSource] = useState(null);
  const chatBottomRef = useRef(null);

  const scrollToBottom = () => {
    if (chatBottomRef.current) {
      chatBottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSend = async (e) => {
    e.preventDefault();
    const query = inputQuery.trim();
    if (!query || loading) return;

    const userMsg = { sender: 'user', text: query };
    setMessages((prev) => [...prev, userMsg]);
    setInputQuery('');
    setLoading(true);
    setError(null);

    try {
      const chatHistory = messages
        .filter(m => !m.isError)
        .map(m => ({
          role: m.sender,
          content: m.text
        }));

      const data = await queryRag(query, 5, language, chatHistory);
      
      const assistantMsg = {
        sender: 'assistant',
        text: data.answer || 'No answer returned.',
        sources: data.sources || [],
        retrievedChunks: data.retrieved_chunks || 0
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      console.error('RAG Query error:', err);
      setError(err.message || 'Failed to generate RAG response.');
      setMessages((prev) => [
        ...prev,
        {
          sender: 'assistant',
          text: `⚠️ Error: ${err.message || 'Unable to communicate with Groq LLM service.'}`,
          sources: [],
          isError: true
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full w-full relative" style={{ background: 'var(--surface-base)' }}>
      
      {/* Messages */}
      <div className="flex-1 overflow-y-auto w-full pt-8 pb-48">
        <div className="max-w-3xl mx-auto px-4 md:px-0 flex flex-col gap-8">
          
          {messages.length === 1 && (
            <div className="flex flex-col items-center justify-center text-center mt-20 mb-8" style={{ animation: 'fadeIn 0.6s ease-out' }}>
              <div className="w-16 h-16 rounded-2xl flex items-center justify-center mb-6"
                style={{ background: 'linear-gradient(135deg, var(--accent-blue), var(--accent-purple))', boxShadow: '0 8px 32px var(--glow-blue)' }}>
                <ShieldCheck size={32} className="text-white" />
              </div>
              <h2 className="text-2xl font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>How can I help you today?</h2>
              <p className="text-sm" style={{ color: 'var(--text-muted)' }}>Ask about BIS standards, compliance, or certifications</p>
            </div>
          )}

          {messages.map((msg, idx) => {
            if (messages.length > 1 && idx === 0 && msg.sender === 'assistant') return null;

            return (
              <div key={idx} className={`flex gap-4 w-full ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                style={{ animation: 'fadeIn 0.3s ease-out' }}>
                
                {msg.sender === 'assistant' && (
                  <div className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0 mt-1"
                    style={{ background: 'linear-gradient(135deg, var(--accent-emerald), #059669)' }}>
                    <Bot size={18} className="text-white" />
                  </div>
                )}

                <div className={`max-w-[85%] ${
                  msg.sender === 'user' 
                    ? 'px-5 py-3.5 rounded-2xl' 
                    : 'py-1'
                }`}
                  style={msg.sender === 'user' ? { 
                    background: 'var(--glass-bg)', 
                    border: '1px solid var(--glass-border)',
                    backdropFilter: 'blur(12px)',
                    color: 'var(--text-primary)'
                  } : { color: 'var(--text-primary)' }}>
                  <div className="prose-custom text-[1rem] leading-7">
                    {msg.sender === 'user' ? (
                      <div className="whitespace-pre-wrap">{msg.text}</div>
                    ) : (
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {msg.text}
                      </ReactMarkdown>
                    )}
                  </div>

                  {msg.sources && msg.sources.length > 0 && (
                    <div className="mt-6 pt-4">
                      <div className="flex flex-wrap gap-2">
                        {msg.sources.map((src, sIdx) => (
                          <button
                            key={sIdx}
                            onClick={() => setSelectedSource(src)}
                            className="flex items-center gap-2 rounded-xl px-3 py-2 text-xs text-left w-full sm:w-auto max-w-xs transition-all duration-200"
                            style={{ 
                              background: 'var(--glass-bg)', 
                              border: '1px solid var(--glass-border)',
                              color: 'var(--text-secondary)'
                            }}
                            onMouseEnter={(e) => e.currentTarget.style.background = 'var(--glass-hover)'}
                            onMouseLeave={(e) => e.currentTarget.style.background = 'var(--glass-bg)'}
                            title="View source document"
                          >
                            <Bookmark size={14} style={{ color: 'var(--accent-blue)' }} className="shrink-0" />
                            <div className="flex flex-col overflow-hidden">
                              <span className="font-semibold truncate" style={{ color: 'var(--text-primary)' }}>{src.document_name}</span>
                              <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Pg {src.page_number} {src.standard_number && src.standard_number !== 'None' ? `• ${src.standard_number}` : ''}</span>
                            </div>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            );
          })}

          {loading && (
            <div className="flex gap-4 w-full" style={{ animation: 'fadeIn 0.3s ease-out' }}>
              <div className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0 mt-1"
                style={{ background: 'linear-gradient(135deg, var(--accent-emerald), #059669)' }}>
                <Bot size={18} className="text-white" />
              </div>
              <div className="flex items-center gap-3 text-sm h-10" style={{ color: 'var(--text-muted)' }}>
                <Loader2 size={18} className="animate-spin" />
              </div>
            </div>
          )}

          <div ref={chatBottomRef} className="h-4" />
        </div>
      </div>

      {/* Input */}
      <div className="absolute bottom-0 left-0 right-0 pt-12 pb-6 px-4"
        style={{ background: `linear-gradient(to top, var(--surface-base), var(--surface-base), transparent)` }}>
        <div className="max-w-3xl mx-auto relative">
          
          {error && (
            <div className="absolute -top-14 left-0 right-0 px-4 py-3 rounded-xl flex items-center gap-2 text-sm"
              style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.25)', color: '#fca5a5' }}>
              <AlertCircle size={16} />
              <span>{error}</span>
            </div>
          )}

          <form 
            onSubmit={handleSend} 
            className="w-full flex items-end gap-2 rounded-2xl p-2 transition-all duration-200"
            style={{ 
              background: 'var(--glass-bg)', 
              border: '1px solid var(--glass-border)',
              backdropFilter: 'blur(16px)',
              boxShadow: '0 8px 32px rgba(0,0,0,0.2)'
            }}
          >
            <textarea
              value={inputQuery}
              onChange={(e) => {
                setInputQuery(e.target.value);
                e.target.style.height = 'auto';
                e.target.style.height = Math.min(e.target.scrollHeight, 200) + 'px';
              }}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSend(e);
                }
              }}
              placeholder="Message BIS Assistant..."
              disabled={loading}
              className="flex-1 bg-transparent text-[1rem] resize-none py-3 px-3 max-h-[200px] overflow-y-auto"
              style={{ color: 'var(--text-primary)', fontFamily: 'inherit', border: 'none', outline: 'none' }}
              rows={1}
            />
            <button 
              type="submit" 
              disabled={loading || !inputQuery.trim()} 
              className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0 mb-1 mr-1 transition-all duration-200"
              style={inputQuery.trim() && !loading ? {
                background: 'linear-gradient(135deg, var(--accent-blue), var(--accent-purple))',
                color: 'white', cursor: 'pointer', border: 'none'
              } : {
                background: 'var(--glass-active)', color: 'var(--text-muted)',
                cursor: 'not-allowed', border: 'none'
              }}
            >
              {loading ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
            </button>
          </form>
          
          <div className="text-center mt-3" style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
            BIS Assistant can make mistakes. Check important info.
          </div>
        </div>
      </div>

      {selectedSource && (
        <SourceViewerModal
          source={selectedSource}
          onClose={() => setSelectedSource(null)}
        />
      )}
    </div>
  );
}
