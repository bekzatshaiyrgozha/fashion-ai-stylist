import React, { useState, useEffect } from 'react';
import {
  adminProductsAPI,
  adminCategoriesAPI,
  adminUsersAPI,
  adminStatsAPI,
} from '../services/api';

export function AdminPage() {
  const [activeTab, setActiveTab] = useState('dashboard');

  return (
    <div className="admin-layout">
      <aside className="admin-sidebar">
        <h2>Admin</h2>
        <button className={`tab-btn ${activeTab === 'dashboard' ? 'active' : ''}`} onClick={() => setActiveTab('dashboard')}>
          Dashboard
        </button>
        <button className={`tab-btn ${activeTab === 'products' ? 'active' : ''}`} onClick={() => setActiveTab('products')}>
          Products
        </button>
        <button className={`tab-btn ${activeTab === 'categories' ? 'active' : ''}`} onClick={() => setActiveTab('categories')}>
          Categories
        </button>
        <button className={`tab-btn ${activeTab === 'users' ? 'active' : ''}`} onClick={() => setActiveTab('users')}>
          Users
        </button>
      </aside>

      <div className="admin-container">
        <h1>Admin Panel</h1>
        <div className="admin-content">
          {activeTab === 'dashboard' && <AdminDashboard />}
          {activeTab === 'products' && <AdminProducts />}
          {activeTab === 'categories' && <AdminCategories />}
          {activeTab === 'users' && <AdminUsers />}
        </div>
      </div>
    </div>
  );
}

function AdminDashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const response = await adminStatsAPI.getStats();
      setStats(response.data);
    } catch (err) {
      console.error('Failed to load stats:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="alert alert-info">Loading...</div>;
  if (!stats) return <div className="alert alert-danger">Failed to load stats</div>;

  return (
    <div className="dashboard-grid">
      <StatCard title="Total Products" value={stats.total_products} icon="📦" />
      <StatCard title="Total Categories" value={stats.total_categories} icon="🏷️" />
      <StatCard title="Total Users" value={stats.total_users} icon="👥" />
      <StatCard title="Admin Users" value={stats.admin_users ?? 0} icon="👮" />
    </div>
  );
}

function StatCard({ title, value, icon }) {
  return (
    <div className="stat-card">
      <div className="stat-icon">{icon}</div>
      <div className="stat-content">
        <p className="stat-title">{title}</p>
        <p className="stat-value">{value}</p>
      </div>
    </div>
  );
}

function AdminProducts() {
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [imageFiles, setImageFiles] = useState({});
  const [uploadingId, setUploadingId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [formImage, setFormImage] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    price: '',
    category_id: '',
    sizes_text: '',
    colors_text: '',
    style_tags_text: '',
    scenarios_text: '',
  });

  useEffect(() => {
    loadProducts();
    loadCategories();
  }, []);

  const parseCsv = (value) =>
    (value || '')
      .split(',')
      .map((x) => x.trim())
      .filter(Boolean);

  const loadCategories = async () => {
    try {
      const response = await adminCategoriesAPI.list();
      setCategories(response.data || []);
    } catch (err) {
      console.error('Failed to load categories:', err);
    }
  };

  const loadProducts = async () => {
    try {
      setLoading(true);
      const response = await adminProductsAPI.list();
      setProducts(response.data);
    } catch (err) {
      setError('Failed to load products');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      setError('');
      setSuccess('');
      const payload = {
        name: formData.name,
        description: formData.description,
        price: parseFloat(formData.price),
        category_id: parseInt(formData.category_id),
        sizes: parseCsv(formData.sizes_text),
        colors: parseCsv(formData.colors_text),
        style_tags: parseCsv(formData.style_tags_text),
        scenarios: parseCsv(formData.scenarios_text),
      };

      if (editingId) {
        await adminProductsAPI.update(editingId, payload);
        if (formImage) {
          await adminProductsAPI.uploadImage(editingId, formImage);
        }
      } else {
        const created = await adminProductsAPI.create(
          payload.name,
          payload.description,
          payload.price,
          payload.category_id,
          payload.sizes,
          payload.colors,
          payload.style_tags,
          payload.scenarios
        );
        const createdId = created?.data?.id;
        if (createdId && formImage) {
          await adminProductsAPI.uploadImage(createdId, formImage);
        }
      }
      loadProducts();
      setShowForm(false);
      setFormImage(null);
      setFormData({
        name: '',
        description: '',
        price: '',
        category_id: '',
        sizes_text: '',
        colors_text: '',
        style_tags_text: '',
        scenarios_text: '',
      });
      setEditingId(null);
      setSuccess('Product saved successfully');
    } catch (err) {
      setError('Failed to save product');
      console.error(err);
    }
  };

  const handleDelete = async (id) => {
    if (confirm('Are you sure?')) {
      try {
        await adminProductsAPI.delete(id);
        loadProducts();
      } catch (err) {
        setError('Failed to delete product');
      }
    }
  };

  const handleUploadImage = async (productId) => {
    const file = imageFiles[productId];
    if (!file) {
      setError('Select image first');
      return;
    }
    try {
      setUploadingId(productId);
      await adminProductsAPI.uploadImage(productId, file);
      setImageFiles((prev) => ({ ...prev, [productId]: undefined }));
      await loadProducts();
    } catch (err) {
      setError('Failed to upload image');
      console.error(err);
    } finally {
      setUploadingId(null);
    }
  };

  if (loading) return <div className="alert alert-info">Loading products...</div>;

  return (
    <div>
      {error && <div className="alert alert-danger">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}
      <button className="btn btn-primary mb-2" onClick={() => setShowForm(!showForm)}>
        {showForm ? 'Cancel' : 'Add Product'}
      </button>

      {showForm && (
        <div className="modal-backdrop" onClick={() => setShowForm(false)}>
          <div className="modal-panel" onClick={(e) => e.stopPropagation()}>
            <div className="modal-head">
              <h3>{editingId ? 'Edit Product' : 'Add Product'}</h3>
              <button className="btn btn-sm btn-outline" onClick={() => setShowForm(false)}>Close</button>
            </div>
            <ProductForm
              initialData={formData}
              onSubmit={handleSubmit}
              onChange={setFormData}
              categories={categories}
              formImage={formImage}
              onImageChange={setFormImage}
            />
          </div>
        </div>
      )}

      <div className="table-responsive">
        <table className="admin-table">
          <thead>
            <tr>
              <th>Photo</th>
              <th>Name</th>
              <th>Brand</th>
              <th>Price</th>
              <th>Stock</th>
              <th>Image</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {products.map((product) => (
              <tr key={product.id}>
                <td>
                  {product.images?.[0] ? (
                    <img src={product.images[0]} alt={product.name} style={{ width: 42, height: 56, objectFit: 'cover' }} />
                  ) : '—'}
                </td>
                <td>{product.name}</td>
                <td>{(product.brand || product.name?.split(' ')[0] || 'Maison').toUpperCase()}</td>
                <td>${product.price.toFixed(2)}</td>
                <td>{product.stock ? 'In Stock' : 'Out of Stock'}</td>
                <td>
                  {product.images?.[0] && (
                    <img src={product.images[0]} alt={product.name} style={{ width: 48, height: 48, objectFit: 'cover', borderRadius: 6, marginRight: 8 }} />
                  )}
                  <input
                    type="file"
                    accept="image/*"
                    onChange={(e) =>
                      setImageFiles((prev) => ({
                        ...prev,
                        [product.id]: e.target.files?.[0],
                      }))
                    }
                  />
                  <button
                    className="btn btn-sm btn-outline"
                    onClick={() => handleUploadImage(product.id)}
                    disabled={uploadingId === product.id}
                  >
                    {uploadingId === product.id ? 'Uploading...' : 'Upload'}
                  </button>
                </td>
                <td>
                  <button
                    className="btn btn-sm btn-secondary"
                    onClick={() => {
                      setFormData({
                        name: product.name || '',
                        description: product.description || '',
                        price: product.price ?? '',
                        category_id: product.category_id ?? '',
                        sizes_text: (product.sizes || []).join(', '),
                        colors_text: (product.colors || []).join(', '),
                        style_tags_text: (product.style_tags || []).join(', '),
                        scenarios_text: (product.scenarios || []).join(', '),
                      });
                      setEditingId(product.id);
                      setFormImage(null);
                      setShowForm(true);
                    }}
                  >
                    EDIT
                  </button>
                  <button
                    className="btn btn-sm btn-danger"
                    onClick={() => handleDelete(product.id)}
                  >
                    DELETE
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ProductForm({ initialData, onSubmit, onChange, categories, formImage, onImageChange }) {
  const handleDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (file) onImageChange(file);
  };

  return (
    <form onSubmit={onSubmit} className="admin-form">
      <div className="form-group">
        <label>Name</label>
        <input
          type="text"
          value={initialData.name}
          onChange={(e) => onChange({ ...initialData, name: e.target.value })}
          required
        />
      </div>
      <div className="form-group">
        <label>Description</label>
        <textarea
          value={initialData.description}
          onChange={(e) => onChange({ ...initialData, description: e.target.value })}
          required
        />
      </div>
      <div className="form-group">
        <label>Price</label>
        <input
          type="number"
          value={initialData.price}
          onChange={(e) => onChange({ ...initialData, price: e.target.value })}
          min="0"
          step="0.01"
          required
        />
      </div>
      <div className="form-group">
        <label>Category</label>
        <select
          value={initialData.category_id}
          onChange={(e) => onChange({ ...initialData, category_id: e.target.value })}
          required
        >
          <option value="">Select category</option>
          {categories.map((cat) => (
            <option key={cat.id} value={cat.id}>
              {cat.name} ({cat.id})
            </option>
          ))}
        </select>
      </div>
      <div className="form-group">
        <label>Sizes (comma separated)</label>
        <input
          type="text"
          value={initialData.sizes_text}
          onChange={(e) => onChange({ ...initialData, sizes_text: e.target.value })}
          placeholder="S, M, L"
        />
      </div>
      <div className="form-group">
        <label>Colors (comma separated)</label>
        <input
          type="text"
          value={initialData.colors_text}
          onChange={(e) => onChange({ ...initialData, colors_text: e.target.value })}
          placeholder="black, white"
        />
      </div>
      <div className="form-group">
        <label>Style tags (comma separated)</label>
        <input
          type="text"
          value={initialData.style_tags_text}
          onChange={(e) => onChange({ ...initialData, style_tags_text: e.target.value })}
          placeholder="casual, office"
        />
      </div>
      <div className="form-group">
        <label>Scenarios (comma separated)</label>
        <input
          type="text"
          value={initialData.scenarios_text}
          onChange={(e) => onChange({ ...initialData, scenarios_text: e.target.value })}
          placeholder="daily, work"
        />
      </div>
      <div className="form-group">
        <label>Product photo</label>
        <div
          className="drop-upload"
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleDrop}
        >
          <input
            type="file"
            accept="image/*"
            onChange={(e) => onImageChange(e.target.files?.[0] || null)}
          />
          <p>Drag & Drop product photo here</p>
        </div>
        {formImage && <p style={{ marginTop: 6, fontSize: 12 }}>Selected: {formImage.name}</p>}
      </div>
      <button type="submit" className="btn btn-success">
        Save Product
      </button>
    </form>
  );
}

function AdminCategories() {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({ name: '', slug: '' });

  useEffect(() => {
    loadCategories();
  }, []);

  const loadCategories = async () => {
    try {
      setLoading(true);
      const response = await adminCategoriesAPI.list();
      setCategories(response.data);
    } catch (err) {
      console.error('Failed to load categories:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await adminCategoriesAPI.create(formData.name, formData.slug);
      loadCategories();
      setShowForm(false);
      setFormData({ name: '', slug: '' });
    } catch (err) {
      console.error('Failed to save category:', err);
    }
  };

  const handleDelete = async (id) => {
    if (confirm('Are you sure?')) {
      try {
        await adminCategoriesAPI.delete(id);
        loadCategories();
      } catch (err) {
        console.error('Failed to delete category:', err);
      }
    }
  };

  if (loading) return <div className="alert alert-info">Loading categories...</div>;

  return (
    <div>
      <button className="btn btn-primary mb-2" onClick={() => setShowForm(!showForm)}>
        {showForm ? 'Cancel' : 'Add Category'}
      </button>

      {showForm && (
        <form onSubmit={handleSubmit} className="admin-form">
          <div className="form-group">
            <label>Name</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
            />
          </div>
          <div className="form-group">
            <label>Slug</label>
            <input
              type="text"
              value={formData.slug}
              onChange={(e) => setFormData({ ...formData, slug: e.target.value })}
              required
            />
          </div>
          <button type="submit" className="btn btn-success">
            Save Category
          </button>
        </form>
      )}

      <div className="table-responsive">
        <table className="admin-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Slug</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {categories.map((cat) => (
              <tr key={cat.id}>
                <td>{cat.name}</td>
                <td>{cat.slug}</td>
                <td>
                  <button
                    className="btn btn-sm btn-danger"
                    onClick={() => handleDelete(cat.id)}
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function AdminUsers() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    try {
      setLoading(true);
      const response = await adminUsersAPI.list();
      setUsers(response.data);
    } catch (err) {
      console.error('Failed to load users:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRoleChange = async (userId, newRole) => {
    try {
      await adminUsersAPI.updateRole(userId, newRole);
      loadUsers();
    } catch (err) {
      console.error('Failed to update user role:', err);
    }
  };

  const handleDelete = async (userId) => {
    if (confirm('Are you sure?')) {
      try {
        await adminUsersAPI.delete(userId);
        loadUsers();
      } catch (err) {
        console.error('Failed to delete user:', err);
      }
    }
  };

  if (loading) return <div className="alert alert-info">Loading users...</div>;

  return (
    <div className="table-responsive">
      <table className="admin-table">
        <thead>
          <tr>
            <th>Email</th>
            <th>Name</th>
            <th>Role</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {users.map((user) => (
            <tr key={user.id}>
              <td>{user.email}</td>
              <td>{user.first_name} {user.last_name}</td>
              <td>
                <select
                  value={user.role || 'user'}
                  onChange={(e) => handleRoleChange(user.id, e.target.value)}
                  className="role-select"
                >
                  <option value="user">User</option>
                  <option value="admin">Admin</option>
                </select>
              </td>
              <td>
                <button
                  className="btn btn-sm btn-danger"
                  onClick={() => handleDelete(user.id)}
                >
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

const adminStyles = `
.admin-layout {
  display: grid;
  grid-template-columns: 250px 1fr;
  gap: 1rem;
}

.admin-sidebar {
  background: var(--card);
  border: 1px solid var(--border);
  padding: 1rem;
  height: fit-content;
  position: sticky;
  top: 98px;
}

.admin-sidebar h2 {
  color: var(--gold);
  margin-bottom: 0.8rem;
}

.admin-container {
  width: 100%;
}

.tab-btn {
  width: 100%;
  background: #101010;
  border: 1px solid var(--border);
  padding: 0.75rem;
  margin-bottom: 0.5rem;
  text-align: left;
  cursor: pointer;
  font-size: 0.74rem;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  transition: all 0.2s;
}

.tab-btn:hover {
  color: var(--gold);
}

.tab-btn.active {
  color: var(--gold);
  border-color: var(--gold);
}

.admin-content {
  background: var(--card);
  padding: 1.2rem;
  border: 1px solid var(--border);
}

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-top: 1rem;
}

.stat-card {
  background: #101010;
  color: var(--text);
  padding: 1.1rem;
  border: 1px solid var(--border);
  display: flex;
  gap: 1rem;
  align-items: center;
}

.stat-icon {
  font-size: 2.5rem;
}

.stat-content {
  flex: 1;
}

.stat-title {
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  opacity: 0.9;
  margin: 0;
}

.stat-value {
  font-size: 1.7rem;
  font-weight: 600;
  color: var(--gold);
  margin: 0;
}

.admin-form {
  background: #101010;
  border: 1px solid var(--border);
  padding: 1.5rem;
  margin-bottom: 2rem;
}

.admin-form .form-group {
  margin-bottom: 1rem;
}

.table-responsive {
  overflow-x: auto;
  margin-top: 1rem;
}

.admin-table {
  width: 100%;
  border-collapse: collapse;
}

.admin-table th,
.admin-table td {
  padding: 1rem;
  text-align: left;
  border-bottom: 1px solid var(--border);
}

.admin-table th {
  background: #101010;
  font-weight: 600;
  color: var(--gold);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-size: 0.72rem;
}

.admin-table tr:hover {
  background: #0f0f0f;
}

.admin-table td {
  color: var(--muted);
}

.admin-table .btn {
  margin-right: 0.5rem;
}

.role-select {
  padding: 0.4rem;
  border: 1px solid var(--border);
  border-radius: 0;
  font-size: 0.9rem;
}

.mb-2 {
  margin-bottom: 1rem;
}

.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.65);
  backdrop-filter: blur(4px);
  display: grid;
  place-items: center;
  z-index: 300;
}

.modal-panel {
  width: min(760px, 94vw);
  max-height: 90vh;
  overflow: auto;
  background: var(--card);
  border: 1px solid var(--border);
  padding: 1rem;
}

.modal-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.drop-upload {
  border: 1px dashed var(--gold);
  padding: 0.75rem;
  text-align: center;
}

.drop-upload p {
  margin: 0.5rem 0 0;
  font-size: 0.78rem;
}

@media (max-width: 920px) {
  .admin-layout {
    grid-template-columns: 1fr;
  }

  .admin-sidebar {
    position: static;
  }
}
`;

export const AdminStyles = () => <style>{adminStyles}</style>;
