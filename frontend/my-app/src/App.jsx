import React, { useState, useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Header from './components/Header';
import LoadingSpinner from './components/LoadingSpinner';
import ProtectedRoute from './components/ProtectedRoute';
import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';
import Interview from './pages/Interview';
import Dashboard from './pages/Dashboard';
import AnswerDetail from './pages/AnswerDetail';

function App() {
  const [loading, setLoading] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState('Memproses permintaan Anda...');

  // Global loading functions
  const showLoading = (message = 'Memproses permintaan Anda...') => {
    setLoadingMessage(message);
    setLoading(true);
  };

  const hideLoading = () => {
    setLoading(false);
  };

  // Make loading functions globally accessible
  useEffect(() => {
    window.showLoading = showLoading;
    window.hideLoading = hideLoading;
    
    return () => {
      delete window.showLoading;
      delete window.hideLoading;
    };
  }, []);

  return (
    <div className="App">
      <LoadingSpinner active={loading} message={loadingMessage} />
      <Header />
      
      <div className="container mt-4">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          
          {/* Protected Routes */}
          <Route 
            path="/interview" 
            element={
              <ProtectedRoute>
                <Interview />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/dashboard" 
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/answer/:id" 
            element={
              <ProtectedRoute>
                <AnswerDetail />
              </ProtectedRoute>
            } 
          />
          
          {/* Redirect unknown routes */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </div>
  );
}

export default App;