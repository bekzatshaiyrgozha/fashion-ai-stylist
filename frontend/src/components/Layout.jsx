import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import '../styles/layout.css';

export function Navbar({ user, onLogout }) {
  const navigate = useNavigate();
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setIsScrolled(window.scrollY > 12);
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const handleLogout = () => {
    onLogout();
    navigate('/login');
  };

  return (
    <nav className={`navbar ${isScrolled ? 'navbar-scrolled' : ''}`}>
      <div className="navbar-container">
        <Link to="/" className="navbar-brand">
          <span className="logo-icon">◇</span>
          <span className="logo-text">FASHION AI</span>
        </Link>

        <ul className="navbar-menu nav-center">
          <li><Link to="/">Home</Link></li>
          <li><Link to="/products">Shop</Link></li>
          <li><Link to="/try-on">Try-On</Link></li>
          <li><Link to="/outfit">Outfit Generator</Link></li>
          {user?.is_admin && (
            <li><Link to="/admin">Admin</Link></li>
          )}
        </ul>

        <ul className="navbar-menu nav-right">
          {user ? (
            <li className="navbar-user">
              <Link to="/profile" className="icon-link" title="Profile">◌</Link>
              <span className="icon-link" title="Cart">⌂</span>
              <button onClick={handleLogout} className="btn btn-sm btn-outline">
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
        <p>© 2026 FASHION AI</p>
      </div>
    </footer>
  );
}

export function Layout({ children, user, onLogout }) {
  return (
    <div className="layout">
      <Navbar user={user} onLogout={onLogout} />
      <main className="main-content">
        <div className="container fade-in-up">{children}</div>
      </main>
      <Footer />
    </div>
  );
}
