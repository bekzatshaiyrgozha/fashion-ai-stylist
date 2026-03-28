import axios from 'axios';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  withCredentials: true, // Send cookies with requests
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Do not force hard redirect here; route guards handle auth state.
    // Hard reload on 401 can cause infinite navigation loops.
    return Promise.reject(error);
  }
);

// Auth endpoints
export const authAPI = {
  register: (email, password, firstName, lastName) =>
    api.post('/auth/register', {
      email,
      password,
      first_name: firstName,
      last_name: lastName,
    }),
  
  login: (email, password) =>
    api.post('/auth/login', { email, password }),

  logout: () =>
    api.post('/auth/logout'),

  bootstrapAdmin: () =>
    api.post('/auth/bootstrap-admin'),
  
  profile: () =>
    api.get('/auth/profile'),
};

// Products endpoints
export const productsAPI = {
  list: (category = null, color = null, size = null, minPrice = null, maxPrice = null) => {
    const params = {};
    if (category) params.category = category;
    if (color) params.color = color;
    if (size) params.size = size;
    if (minPrice !== null) params.min_price = minPrice;
    if (maxPrice !== null) params.max_price = maxPrice;
    return api.get('/products/', { params });
  },
  
  getById: (productId) =>
    api.get(`/products/${productId}`),
};

// Categories endpoints
export const categoriesAPI = {
  list: () =>
    api.get('/categories/'),
};

// Outfit endpoints
export const outfitAPI = {
  generate: (style, scenario, sizes, colors) =>
    api.post('/outfit/generate', {
      style,
      scenario,
      sizes,
      colors,
    }),
  
  history: () =>
    api.get('/outfit/history'),
};

// Try-on endpoints
export const tryonAPI = {
  upload: (userPhoto, productId, clothingType = 'top') => {
    const formData = new FormData();
    formData.append('user_photo', userPhoto);
    formData.append('product_id', String(productId));
    formData.append('clothing_type', clothingType);
    return api.post('/tryon/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  preview: (userPhoto, clothingPhoto, clothingType = 'top') => {
    const formData = new FormData();
    formData.append('user_photo', userPhoto);
    formData.append('clothing_photo', clothingPhoto);
    formData.append('clothing_type', clothingType);
    return api.post('/tryon/preview', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
};

// Admin - Products endpoints
export const adminProductsAPI = {
  list: (skip = 0, limit = 10) =>
    api.get('/admin/products/', { params: { skip, limit } }),
  
  getById: (productId) =>
    api.get(`/admin/products/${productId}`),
  
  create: (name, description, price, categoryId, sizes, colors, styleTags, scenarios) =>
    api.post('/admin/products/', {
      name,
      description,
      price,
      category_id: categoryId,
      sizes,
      colors,
      style_tags: styleTags,
      scenarios,
    }),
  
  update: (productId, updates) =>
    api.put(`/admin/products/${productId}`, updates),
  
  delete: (productId) =>
    api.delete(`/admin/products/${productId}`),
  
  uploadImage: (productId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post(`/admin/products/${productId}/image`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  
  updateStock: (productId, stock) =>
    api.patch(`/admin/products/${productId}/stock`, { stock }),
};

// Admin - Categories endpoints
export const adminCategoriesAPI = {
  list: (skip = 0, limit = 10) =>
    api.get('/admin/categories/', { params: { skip, limit } }),
  
  getById: (categoryId) =>
    api.get(`/admin/categories/${categoryId}`),
  
  create: (name, slug) =>
    api.post('/admin/categories/', { name, slug }),
  
  update: (categoryId, name, slug) =>
    api.put(`/admin/categories/${categoryId}`, { name, slug }),
  
  delete: (categoryId) =>
    api.delete(`/admin/categories/${categoryId}`),
};

// Admin - Users endpoints
export const adminUsersAPI = {
  list: (skip = 0, limit = 10) =>
    api.get('/admin/users/', { params: { skip, limit } }),
  
  getById: (userId) =>
    api.get(`/admin/users/${userId}`),
  
  updateRole: (userId, role) =>
    api.patch(`/admin/users/${userId}/role`, { role }),
  
  delete: (userId) =>
    api.delete(`/admin/users/${userId}`),
};

// Admin - Stats endpoints
export const adminStatsAPI = {
  getStats: () =>
    api.get('/admin/stats/'),
};

// Health check
export const systemAPI = {
  health: () =>
    api.get('/health'),
};

export default api;
