import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  ShieldCheck, MessageSquare, ClipboardCheck, Database, Search,
  Globe, LogOut, Shield, Menu, X
} from 'lucide-react';

import ChatAssistant from '../components/ChatAssistant';
import ComplianceInspector from '../components/ComplianceInspector';
import PdfUpload from '../components/PdfUpload';
import DocumentList from '../components/DocumentList';
import VectorSearchTester from '../components/VectorSearchTester';

const NAV_ITEMS = [
  { id: 'chat', label: 'Chat', icon: MessageSquare, path: '/admin' },
  { id: 'inspector', label: 'Inspector', icon: ClipboardCheck, path: '/admin/inspector' },
  { id: 'knowledge', label: 'Knowledge Base', icon: Database, path: '/admin/knowledge', admin: true },
  { id: 'vector', label: 'Vector Search', icon: Search, path: '/admin/vector', admin: true },
];

export default function AdminDashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [selectedLanguage, setSelectedLanguage] = useState('English');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [documents, setDocuments] = useState([]);
  const [loadingDocs, setLoadingDocs] = useState(false);

  const getActiveTab = () => {
    if (location.pathname.includes('/admin/inspector')) return 'inspector';
    if (location.pathname.includes('/admin/knowledge')) return 'knowledge';
    if (location.pathname.includes('/admin/vector')) return 'vector';
    return 'chat';
  };
  const activeTab = getActiveTab();

  const loadDocumentsList = async () => {
    setLoadingDocs(true);
    try {
      const response = await fetch('http://localhost:8000/api/documents');
      if (response.ok) {
        const data = await response.json();
        setDocuments(Array.isArray(data) ? data : (data.documents || []));
      }
    } catch (error) {
      console.error("Failed to load documents:", error);
    } finally {
      setLoadingDocs(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'knowledge') loadDocumentsList();
  }, [activeTab]);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <div className="dashboard-layout">
      <aside className={`dashboard-sidebar admin-sidebar ${mobileMenuOpen ? 'mobile-open' : ''}`}>
        <div className="sidebar-inner">
          <div className="sidebar-brand">
            <div className="sidebar-brand-icon admin-icon">
              <ShieldCheck size={20} />
            </div>
            <div className="sidebar-brand-text">
              <span className="sidebar-brand-name">BIS Assistant</span>
              <span className="sidebar-brand-tag admin-tag">Admin Panel</span>
            </div>
            <button className="mobile-close-btn" onClick={() => setMobileMenuOpen(false)}>
              <X size={20} />
            </button>
          </div>

          <nav className="sidebar-nav">
            {NAV_ITEMS.map((item) => (
              <button
                key={item.id}
                onClick={() => { navigate(item.path); setMobileMenuOpen(false); }}
                className={`sidebar-nav-item ${activeTab === item.id ? 'active' : ''} ${item.admin ? 'admin-item' : ''}`}
              >
                <item.icon size={18} />
                <span>{item.label}</span>
                {item.admin && <span className="admin-badge">Admin</span>}
              </button>
            ))}
          </nav>

          <div className="sidebar-section">
            <div className="sidebar-lang">
              <Globe size={16} />
              <select
                value={selectedLanguage}
                onChange={(e) => setSelectedLanguage(e.target.value)}
                className="sidebar-lang-select"
              >
                <option value="English">English</option>
                <option value="Hindi">Hindi</option>
                <option value="Marathi">Marathi</option>
              </select>
            </div>
          </div>

          <div className="sidebar-footer">
            <div className="sidebar-user">
              <div className="sidebar-user-avatar admin-avatar">
                <Shield size={16} />
              </div>
              <div className="sidebar-user-info">
                <span className="sidebar-user-name">{user?.name || user?.email}</span>
                <span className="sidebar-user-role admin-role">Administrator</span>
              </div>
            </div>
            <button onClick={handleLogout} className="sidebar-logout-btn">
              <LogOut size={18} />
              <span>Logout</span>
            </button>
          </div>
        </div>
      </aside>

      {mobileMenuOpen && <div className="sidebar-overlay" onClick={() => setMobileMenuOpen(false)} />}

      <main className="dashboard-main">
        <header className="dashboard-mobile-header">
          <button onClick={() => setMobileMenuOpen(true)} className="mobile-menu-btn">
            <Menu size={22} />
          </button>
          <div className="mobile-brand">
            <ShieldCheck size={18} className="text-amber-400" />
            <span>Admin Panel</span>
          </div>
        </header>

        <div className="dashboard-content">
          {activeTab === 'chat' && <ChatAssistant language={selectedLanguage} />}
          {activeTab === 'inspector' && (
            <div className="page-scroll-container">
              <ComplianceInspector />
            </div>
          )}
          {activeTab === 'knowledge' && (
            <div className="page-scroll-container">
              <div className="glass-page-wrapper">
                <div className="glass-page-header">
                  <h2>Knowledge Base</h2>
                  <p>Upload and manage vectorized BIS standard documents.</p>
                </div>
                <PdfUpload onUploadSuccess={loadDocumentsList} />
                <DocumentList
                  documents={documents}
                  loading={loadingDocs}
                  onRefresh={loadDocumentsList}
                />
              </div>
            </div>
          )}
          {activeTab === 'vector' && (
            <div className="page-scroll-container">
              <VectorSearchTester />
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
