import React, { useState, useRef, useEffect } from 'react';
import { ShieldCheck, Send, Bot, FileText, Bookmark, Loader2, AlertCircle } from 'lucide-react';
import { queryRag } from '../services/api';
import SourceViewerModal from './SourceViewerModal';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export default function ChatAssistant({ language = 'English' }) {
  const [messages, setMessages] = useState([
    {
      sender: 'assistant',
      text: 'Hello! I am your AI-Powered BIS Standards Assistant. Ask me any question regarding your uploaded official Bureau of Indian Standards (BIS) documents.',
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
      // Filter out error messages and format for backend
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
    <div className="flex flex-col h-full w-full relative bg-[#212121]">
      
      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto w-full pt-8 pb-48">
        <div className="max-w-3xl mx-auto px-4 md:px-0 flex flex-col gap-8">
          
          {/* Empty State */}
          {messages.length === 1 && (
            <div className="flex flex-col items-center justify-center text-center mt-20 mb-8">
              <div className="w-16 h-16 rounded-full bg-[#2f2f2f] flex items-center justify-center mb-6">
                <ShieldCheck size={32} className="text-gray-200" />
              </div>
              <h2 className="text-2xl font-semibold text-gray-100 mb-2">How can I help you today?</h2>
            </div>
          )}

          {/* Messages */}
          {messages.map((msg, idx) => {
            if (messages.length > 1 && idx === 0 && msg.sender === 'assistant') return null;

            return (
              <div key={idx} className={`flex gap-4 w-full ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                
                {msg.sender === 'assistant' && (
                  <div className="w-8 h-8 rounded-full bg-green-700 flex items-center justify-center shrink-0 mt-1">
                    <Bot size={18} className="text-white" />
                  </div>
                )}

                <div className={`max-w-[85%] ${
                  msg.sender === 'user' 
                    ? 'bg-[#2f2f2f] px-5 py-3.5 rounded-2xl text-gray-100' 
                    : 'text-gray-100 py-1'
                }`}>
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
                            className="flex items-center gap-2 bg-[#2f2f2f] hover:bg-[#3f3f3f] border border-white/10 rounded-xl px-3 py-2 text-gray-300 transition-colors text-xs text-left w-full sm:w-auto max-w-xs"
                            title="View source document"
                          >
                            <Bookmark size={14} className="text-gray-400 shrink-0" />
                            <div className="flex flex-col overflow-hidden">
                              <span className="font-semibold text-gray-200 truncate">{src.document_name}</span>
                              <span className="text-[10px] text-gray-400">Pg {src.page_number} {src.standard_number && src.standard_number !== 'None' ? `• ${src.standard_number}` : ''}</span>
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
            <div className="flex gap-4 w-full">
              <div className="w-8 h-8 rounded-full bg-green-700 flex items-center justify-center shrink-0 mt-1">
                <Bot size={18} className="text-white" />
              </div>
              <div className="flex items-center gap-3 text-sm text-gray-400 h-10">
                <Loader2 size={18} className="animate-spin" />
              </div>
            </div>
          )}

          <div ref={chatBottomRef} className="h-4" />
        </div>
      </div>

      {/* Fixed Bottom Input Area */}
      <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-[#212121] via-[#212121] to-transparent pt-12 pb-6 px-4">
        <div className="max-w-3xl mx-auto relative">
          
          {error && (
            <div className="absolute -top-14 left-0 right-0 bg-red-900/50 border border-red-500 text-red-200 px-4 py-3 rounded-xl flex items-center gap-2 text-sm">
              <AlertCircle size={16} />
              <span>{error}</span>
            </div>
          )}

          <form 
            onSubmit={handleSend} 
            className="w-full flex items-end gap-2 bg-[#2f2f2f] rounded-2xl p-2 shadow-[0_0_15px_rgba(0,0,0,0.1)] border border-white/5 focus-within:border-white/20 transition-colors"
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
              className="flex-1 bg-transparent text-gray-100 placeholder-gray-400 text-[1rem] resize-none outline-none py-3 px-3 max-h-[200px] overflow-y-auto"
              rows={1}
            />
            <button 
              type="submit" 
              disabled={loading || !inputQuery.trim()} 
              className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 mb-1 mr-1 transition-colors ${
                inputQuery.trim() && !loading
                  ? 'bg-white text-black hover:bg-gray-200'
                  : 'bg-[#424242] text-gray-500 cursor-not-allowed'
              }`}
            >
              {loading ? <Loader2 size={18} className="animate-spin text-gray-400" /> : <Send size={18} />}
            </button>
          </form>
          
          <div className="text-center mt-3 text-[11px] text-gray-400">
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
