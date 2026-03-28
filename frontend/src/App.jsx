import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/Layout';
import { LoginPage, RegisterPage, ProfilePage, AuthStyles } from './pages/Auth';
import { ProductsPage, ProductDetailPage, ProductsStyles } from './pages/Products';
import { OutfitGeneratorPage, OutfitStyles } from './pages/Outfit';
import { AdminPage, AdminStyles } from './pages/Admin';
import { HomePage } from './pages/Home';
import { authAPI } from './services/api';
import './styles/global.css';

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      const response = await authAPI.profile();
      setUser(response.data);
      setIsAuthenticated(true);
    } catch (err) {
      setUser(null);
      setIsAuthenticated(false);
    } finally {
      setLoading(false);
    }
  };

  const handleLoginSuccess = async () => {
    try {
      const response = await authAPI.profile();
      setUser(response.data);
      setIsAuthenticated(true);
    } catch (err) {
      console.error('Failed to fetch user profile:', err);
    }
  };

  const handlePromoteAdmin = async () => {
    await authAPI.bootstrapAdmin();
    await handleLoginSuccess();
  };

  const handleLogout = () => {
    authAPI.logout().finally(() => {
      setUser(null);
      setIsAuthenticated(false);
    });
  };

  const ProtectedRoute = ({ children }) => {
    if (!isAuthenticated) {
      return <Navigate to="/login" />;
    }
    return children;
  };

  const AdminRoute = ({ children }) => {
    if (!isAuthenticated || !user?.is_admin) {
      return <Navigate to="/" />;
    }
    return children;
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '2rem' }}>
        <div className="spinner"></div>
        <p>Loading...</p>
      </div>
    );
  }

  return (
    <Router>
      <Layout user={user} onLogout={handleLogout}>
        <AuthStyles />
        <ProductsStyles />
        <OutfitStyles />
        <AdminStyles />
        
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/login" element={<LoginPage onLoginSuccess={handleLoginSuccess} />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route
            path="/profile"
            element={
              <ProtectedRoute>
                <ProfilePage user={user} onPromoteAdmin={handlePromoteAdmin} />
              </ProtectedRoute>
            }
          />
          <Route path="/products" element={<ProductsPage />} />
          <Route path="/products/:id" element={<ProductDetailPage />} />
          <Route
            path="/outfit"
            element={
              <ProtectedRoute>
                <OutfitGeneratorPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin"
            element={
              <AdminRoute>
                <AdminPage />
              </AdminRoute>
            }
          />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
