import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';

import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import UserDashboard from './pages/UserDashboard';
import AdminDashboard from './pages/AdminDashboard';

function AuthRedirect() {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (!user) return <Navigate to="/login" replace />;
  return user.role === 'ADMIN' ? <Navigate to="/admin" replace /> : <Navigate to="/chat" replace />;
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          {/* User Routes */}
          <Route path="/chat" element={
            <ProtectedRoute><UserDashboard /></ProtectedRoute>
          } />
          <Route path="/inspector" element={
            <ProtectedRoute><UserDashboard /></ProtectedRoute>
          } />

          {/* Admin Routes */}
          <Route path="/admin" element={
            <ProtectedRoute adminOnly><AdminDashboard /></ProtectedRoute>
          } />
          <Route path="/admin/inspector" element={
            <ProtectedRoute adminOnly><AdminDashboard /></ProtectedRoute>
          } />
          <Route path="/admin/knowledge" element={
            <ProtectedRoute adminOnly><AdminDashboard /></ProtectedRoute>
          } />
          <Route path="/admin/vector" element={
            <ProtectedRoute adminOnly><AdminDashboard /></ProtectedRoute>
          } />

          {/* Default */}
          <Route path="*" element={<AuthRedirect />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
