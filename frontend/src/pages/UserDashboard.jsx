import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  ShieldCheck, MessageSquare, ClipboardCheck, Globe, LogOut, User, Menu, X
} from 'lucide-react';

import ChatAssistant from '../components/ChatAssistant';
import ComplianceInspector from '../components/ComplianceInspector';

const NAV_ITEMS = [
  { id: 'chat', label: 'Chat', icon: MessageSquare, path: '/chat' },
  { id: 'inspector', label: 'Inspector', icon: ClipboardCheck, path: '/inspector' },
];

export default function UserDashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [selectedLanguage, setSelectedLanguage] = useState('English');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Derive active tab from URL
  const activeTab = location.pathname.includes('inspector') ? 'inspector' : 'chat';

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <div className="dashboard-layout">
      {/* Sidebar */}
      <aside className={`dashboard-sidebar ${mobileMenuOpen ? 'mobile-open' : ''}`}>
        <div className="sidebar-inner">
          {/* Brand */}
          <div className="sidebar-brand">
            <div className="sidebar-brand-icon">
              <ShieldCheck size={20} />
            </div>
            <div className="sidebar-brand-text">
              <span className="sidebar-brand-name">BIS Assistant</span>
              <span className="sidebar-brand-tag">Standards AI</span>
            </div>
            <button className="mobile-close-btn" onClick={() => setMobileMenuOpen(false)}>
              <X size={20} />
            </button>
          </div>

          {/* Navigation */}
          <nav className="sidebar-nav">
            {NAV_ITEMS.map((item) => (
              <button
                key={item.id}
                onClick={() => { navigate(item.path); setMobileMenuOpen(false); }}
                className={`sidebar-nav-item ${activeTab === item.id ? 'active' : ''}`}
              >
                <item.icon size={18} />
                <span>{item.label}</span>
              </button>
            ))}
          </nav>

          {/* Language */}
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

          {/* User Info + Logout */}
          <div className="sidebar-footer">
            <div className="sidebar-user">
              <div className="sidebar-user-avatar">
                <User size={16} />
              </div>
              <div className="sidebar-user-info">
                <span className="sidebar-user-name">{user?.name || user?.email}</span>
                <span className="sidebar-user-role">User</span>
              </div>
            </div>
            <button onClick={handleLogout} className="sidebar-logout-btn">
              <LogOut size={18} />
              <span>Logout</span>
            </button>
          </div>
        </div>
      </aside>

      {/* Overlay for mobile */}
      {mobileMenuOpen && <div className="sidebar-overlay" onClick={() => setMobileMenuOpen(false)} />}

      {/* Main Content */}
      <main className="dashboard-main">
        {/* Mobile Header */}
        <header className="dashboard-mobile-header">
          <button onClick={() => setMobileMenuOpen(true)} className="mobile-menu-btn">
            <Menu size={22} />
          </button>
          <div className="mobile-brand">
            <ShieldCheck size={18} className="text-blue-400" />
            <span>BIS Assistant</span>
          </div>
        </header>

        <div className="dashboard-content">
          {activeTab === 'chat' && <ChatAssistant language={selectedLanguage} />}
          {activeTab === 'inspector' && (
            <div className="page-scroll-container">
              <ComplianceInspector />
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
