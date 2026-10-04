import React, { useState, useEffect } from 'react';
import { 
  ShieldCheck, MessageSquare, ClipboardCheck, 
  Database, Search, Globe, LogIn 
} from 'lucide-react';

import ChatAssistant from './components/ChatAssistant';
import ComplianceInspector from './components/ComplianceInspector';
import PdfUpload from './components/PdfUpload';
import DocumentList from './components/DocumentList';
import VectorSearchTester from './components/VectorSearchTester';

export default function App() {
  const [activeTab, setActiveTab] = useState('chat');
  const [selectedLanguage, setSelectedLanguage] = useState('English');
  const [isAdminMode, setIsAdminMode] = useState(false);
  
  // Knowledge Base State
  const [documents, setDocuments] = useState([]);
  const [loadingDocs, setLoadingDocs] = useState(false);

  const loadDocumentsList = async () => {
    setLoadingDocs(true);
    try {
      const response = await fetch('http://localhost:8000/api/documents');
      if (response.ok) {
        const data = await response.json();
        setDocuments(Array.isArray(data) ? data : (data.documents || []));
      }
    } catch (error) {
      console.error("Failed to load documents list:", error);
    } finally {
      setLoadingDocs(false);
    }
  };

  useEffect(() => {
    if (isAdminMode && activeTab === 'documents') {
      loadDocumentsList();
    }
  }, [isAdminMode, activeTab]);

  return (
    <div className="flex h-screen w-full bg-[#212121] text-gray-100 font-sans overflow-hidden">
      
      {/* Sidebar - ChatGPT Style */}
      <aside className="w-[260px] flex-shrink-0 bg-[#171717] hidden md:flex flex-col justify-between border-r border-white/5">
        <div className="flex flex-col h-full">
          
          {/* Top Branding */}
          <div className="p-4 flex flex-col gap-4">
            <div className="flex items-center gap-3 px-2 py-1">
              <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white">
                <ShieldCheck size={18} />
              </div>
              <div className="flex flex-col">
                <span className="font-semibold text-sm leading-none">BIS Assistant</span>
                <span className="text-[11px] text-gray-400 mt-1">Official Standards AI</span>
              </div>
            </div>

            {/* Main Nav */}
            <nav className="flex flex-col gap-1 mt-4">
              <button
                onClick={() => setActiveTab('chat')}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                  activeTab === 'chat' 
                    ? 'bg-[#2f2f2f] text-white font-medium' 
                    : 'text-gray-300 hover:bg-[#212121]'
                }`}
              >
                <MessageSquare size={16} />
                <span>Chat</span>
              </button>
              
              <button
                onClick={() => setActiveTab('compliance')}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                  activeTab === 'compliance' 
                    ? 'bg-[#2f2f2f] text-white font-medium' 
                    : 'text-gray-300 hover:bg-[#212121]'
                }`}
              >
                <ClipboardCheck size={16} />
                <span>Inspector</span>
              </button>
            </nav>

            {/* Admin Nav */}
            {isAdminMode && (
              <nav className="flex flex-col gap-1 mt-6 border-t border-white/5 pt-4">
                <span className="text-xs font-semibold text-gray-500 px-3 mb-1">Admin Mode</span>
                <button
                  onClick={() => setActiveTab('documents')}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                    activeTab === 'documents' 
                      ? 'bg-[#2f2f2f] text-white font-medium' 
                      : 'text-gray-300 hover:bg-[#212121]'
                  }`}
                >
                  <Database size={16} />
                  <span>Knowledge Base</span>
                </button>
                <button
                  onClick={() => setActiveTab('vectorSearch')}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                    activeTab === 'vectorSearch' 
                      ? 'bg-[#2f2f2f] text-white font-medium' 
                      : 'text-gray-300 hover:bg-[#212121]'
                  }`}
                >
                  <Search size={16} />
                  <span>Vector Search</span>
                </button>
              </nav>
            )}
          </div>
        </div>

        {/* Bottom Footer Area */}
        <div className="p-3 border-t border-white/5 flex flex-col gap-2">
          
          <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-[#212121] text-gray-300">
            <Globe size={14} className="text-gray-400" />
            <select
              value={selectedLanguage}
              onChange={(e) => setSelectedLanguage(e.target.value)}
              className="bg-transparent text-sm w-full outline-none cursor-pointer appearance-none"
            >
              <option value="English" className="bg-[#212121]">English</option>
              <option value="Hindi" className="bg-[#212121]">Hindi</option>
              <option value="Marathi" className="bg-[#212121]">Marathi</option>
            </select>
          </div>

          <button
            onClick={() => {
              const next = !isAdminMode;
              setIsAdminMode(next);
              if (!next && (activeTab === 'documents' || activeTab === 'vectorSearch')) {
                setActiveTab('chat');
              }
            }}
            className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-gray-300 hover:bg-[#212121] transition-colors"
          >
            <LogIn size={16} className={isAdminMode ? 'text-blue-500' : 'text-gray-400'} />
            <span>{isAdminMode ? 'Exit Admin Mode' : 'Admin Login'}</span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col h-full relative bg-[#212121]">
        
        {/* Mobile Header */}
        <header className="md:hidden h-14 border-b border-white/5 flex items-center justify-between px-4 bg-[#171717] shrink-0">
          <div className="flex items-center gap-2">
            <ShieldCheck size={18} className="text-blue-500" />
            <span className="font-semibold text-sm">BIS Assistant</span>
          </div>
          <div className="flex gap-2">
             <button onClick={() => setActiveTab('chat')} className="text-xs text-gray-300 px-2">Chat</button>
             <button onClick={() => setIsAdminMode(!isAdminMode)} className="text-xs text-gray-300 px-2">Admin</button>
          </div>
        </header>

        {/* Content Area */}
        <div className="flex-1 overflow-hidden relative">
          {activeTab === 'chat' && <ChatAssistant language={selectedLanguage} />}
          
          {activeTab === 'compliance' && (
            <div className="h-full overflow-y-auto p-6 md:p-8">
              <ComplianceInspector />
            </div>
          )}

          {isAdminMode && activeTab === 'documents' && (
            <div className="h-full overflow-y-auto p-6 md:p-10 max-w-5xl mx-auto flex flex-col gap-8">
              <div className="pb-4 border-b border-white/10">
                <h2 className="text-2xl font-bold text-gray-100">Knowledge Base</h2>
                <p className="text-gray-400 mt-1">Upload and manage vectorized BIS documents.</p>
              </div>
              <PdfUpload onUploadSuccess={loadDocumentsList} />
              <DocumentList
                documents={documents}
                loading={loadingDocs}
                onRefresh={loadDocumentsList}
              />
            </div>
          )}

          {isAdminMode && activeTab === 'vectorSearch' && (
            <div className="h-full overflow-y-auto p-6 md:p-10">
              <VectorSearchTester />
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
