import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { authAPI } from '../services/api';
import { useForm } from '../hooks';

export function LoginPage({ onLoginSuccess }) {
  const navigate = useNavigate();
  const [apiError, setApiError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const form = useForm(
    { email: '', password: '' },
    async (values) => {
      try {
        setIsLoading(true);
        setApiError('');
        await authAPI.login(values.email, values.password);
        await onLoginSuccess();
        navigate('/');
      } catch (error) {
        const message =
          typeof error.response?.data?.detail === 'string'
            ? error.response.data.detail
            : 'Login failed. Please check your credentials.';
        setApiError(message);
      } finally {
        setIsLoading(false);
      }
    }
  );

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h1>Login</h1>
        {apiError && <div className="alert alert-danger">{apiError}</div>}
        
        <form onSubmit={form.handleSubmit}>
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              name="email"
              value={form.values.email}
              onChange={form.handleChange}
              onBlur={form.handleBlur}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              name="password"
              value={form.values.password}
              onChange={form.handleChange}
              onBlur={form.handleBlur}
              required
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary btn-block btn-lg"
            disabled={isLoading}
          >
            {isLoading ? 'Logging in...' : 'Login'}
          </button>
        </form>

        <p className="auth-link">
          Don't have an account? <Link to="/register">Register here</Link>
        </p>
      </div>
    </div>
  );
}

export function RegisterPage() {
  const navigate = useNavigate();
  const [apiError, setApiError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const form = useForm(
    { email: '', password: '', firstName: '', lastName: '' },
    async (values) => {
      try {
        setIsLoading(true);
        setApiError('');
        await authAPI.register(values.email, values.password, values.firstName, values.lastName);
        navigate('/login');
      } catch (error) {
        const message = error.response?.data?.detail || 'Registration failed. Please try again.';
        setApiError(message);
      } finally {
        setIsLoading(false);
      }
    }
  );

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h1>Register</h1>
        {apiError && <div className="alert alert-danger">{apiError}</div>}
        
        <form onSubmit={form.handleSubmit}>
          <div className="form-group">
            <label htmlFor="firstName">First Name</label>
            <input
              type="text"
              id="firstName"
              name="firstName"
              value={form.values.firstName}
              onChange={form.handleChange}
              onBlur={form.handleBlur}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="lastName">Last Name</label>
            <input
              type="text"
              id="lastName"
              name="lastName"
              value={form.values.lastName}
              onChange={form.handleChange}
              onBlur={form.handleBlur}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              name="email"
              value={form.values.email}
              onChange={form.handleChange}
              onBlur={form.handleBlur}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              name="password"
              value={form.values.password}
              onChange={form.handleChange}
              onBlur={form.handleBlur}
              required
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary btn-block btn-lg"
            disabled={isLoading}
          >
            {isLoading ? 'Registering...' : 'Register'}
          </button>
        </form>

        <p className="auth-link">
          Already have an account? <Link to="/login">Login here</Link>
        </p>
      </div>
    </div>
  );
}

export function ProfilePage({ user, onPromoteAdmin }) {
  const navigate = useNavigate();
  const [promoteLoading, setPromoteLoading] = useState(false);
  const [promoteError, setPromoteError] = useState('');

  if (!user) return <div className="alert alert-warning">Please login first</div>;

  const handlePromote = async () => {
    try {
      setPromoteLoading(true);
      setPromoteError('');
      await onPromoteAdmin();
    } catch (e) {
      setPromoteError(
        typeof e?.response?.data?.detail === 'string'
          ? e.response.data.detail
          : 'Failed to promote user to admin'
      );
    } finally {
      setPromoteLoading(false);
    }
  };

  return (
    <div className="card">
      <h1>Profile</h1>
      <div className="profile-info">
        <p><strong>Name:</strong> {user.first_name} {user.last_name}</p>
        <p><strong>Email:</strong> {user.email}</p>
        <p><strong>Role:</strong> {user.is_admin ? 'Admin' : 'User'}</p>
        <p><strong>Member Since:</strong> {new Date().toLocaleDateString()}</p>
        {!user.is_admin ? (
          <>
            <button className="btn btn-secondary" onClick={handlePromote} disabled={promoteLoading}>
              {promoteLoading ? 'Promoting...' : 'Make me admin'}
            </button>
            {promoteError && <p className="form-error">{promoteError}</p>}
          </>
        ) : (
          <button className="btn btn-primary" onClick={() => navigate('/admin')}>
            Open Admin Panel
          </button>
        )}
      </div>
    </div>
  );
}

const authStyles = `
.auth-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 60vh;
  padding: 2rem;
}

.auth-card {
  background: white;
  padding: 2rem;
  border-radius: 0.5rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 400px;
}

.auth-card h1 {
  text-align: center;
  margin-bottom: 2rem;
}

.auth-link {
  text-align: center;
  margin-top: 1rem;
}

.profile-info p {
  margin-bottom: 1rem;
  font-size: 1.1rem;
}
`;

export const AuthStyles = () => <style>{authStyles}</style>;
