import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import '../styles/layout.css';

export function Navbar({ user, onLogout }) {
  const navigate = useNavigate();

  const handleLogout = () => {
    onLogout();
    navigate('/login');
  };

  return (
    <nav className="navbar">
      <div className="navbar-container">
        <Link to="/" className="navbar-brand">
          👗 Fashion AI Stylist
        </Link>
        <ul className="navbar-menu">
          <li><Link to="/">Home</Link></li>
          <li><Link to="/products">Shop</Link></li>
          <li><Link to="/outfit">Outfit Generator</Link></li>
          {user?.is_admin && (
            <li><Link to="/admin">Admin Panel</Link></li>
          )}
          {user ? (
            <li className="navbar-user">
              <span>{user.email}</span>
              <Link to="/profile" className="btn btn-sm btn-outline">Profile</Link>
              <button onClick={handleLogout} className="btn btn-sm btn-danger">
                Logout
              </button>
            </li>
          ) : (
            <>
              <li><Link to="/login">Login</Link></li>
              <li><Link to="/register">Register</Link></li>
            </>
          )}
        </ul>
      </div>
    </nav>
  );
}

export function Footer() {
  return (
    <footer className="footer">
      <div className="footer-content">
        <div className="footer-section">
          <h4>About</h4>
          <p>AI-powered fashion outfit generation and virtual try-on.</p>
        </div>
        <div className="footer-section">
          <h4>Links</h4>
          <ul>
            <li><Link to="/">Home</Link></li>
            <li><Link to="/products">Products</Link></li>
            <li><Link to="/outfit">Outfit</Link></li>
          </ul>
        </div>
        <div className="footer-section">
          <h4>Contact</h4>
          <p>Email: info@fashionaistylist.com</p>
          <p>Phone: +1 (555) 123-4567</p>
        </div>
      </div>
      <div className="footer-bottom">
        <p>&copy; 2026 Fashion AI Stylist. All rights reserved.</p>
      </div>
    </footer>
  );
}

export function Layout({ children, user, onLogout }) {
  return (
    <div className="layout">
      <Navbar user={user} onLogout={onLogout} />
      <main className="main-content">
        <div className="container">{children}</div>
      </main>
      <Footer />
    </div>
  );
}
