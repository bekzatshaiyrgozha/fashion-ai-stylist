import React, { useState, useEffect } from 'react';
import { productsAPI, categoriesAPI } from '../services/api';
import TryOnModal from '../components/TryOnModal';

export function ProductsPage() {
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [filters, setFilters] = useState({
    category: null,
    color: null,
    size: null,
    minPrice: null,
    maxPrice: null,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadProducts();
    loadCategories();
  }, [filters]);

  const loadCategories = async () => {
    try {
      const response = await categoriesAPI.list();
      setCategories(response.data);
    } catch (err) {
      console.error('Failed to load categories:', err);
    }
  };

  const loadProducts = async () => {
    try {
      setLoading(true);
      setError('');
      const response = await productsAPI.list(
        filters.category,
        filters.color,
        filters.size,
        filters.minPrice,
        filters.maxPrice
      );
      setProducts(response.data);
    } catch (err) {
      setError('Failed to load products');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters((prev) => ({
      ...prev,
      [name]: value === '' ? null : value,
    }));
  };

  return (
    <div>
      <h1>Shop</h1>

      <div className="products-container">
        <aside className="filters-sidebar">
          <h3>Filters</h3>

          <div className="form-group">
            <label htmlFor="categoryId">Category</label>
            <select
              id="categoryId"
              name="category"
              value={filters.category || ''}
              onChange={handleFilterChange}
            >
              <option value="">All Categories</option>
              {categories.map((cat) => (
                <option key={cat.id} value={cat.slug}>
                  {cat.name}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="color">Color</label>
            <input
              type="text"
              id="color"
              name="color"
              placeholder="e.g., blue, red"
              value={filters.color || ''}
              onChange={handleFilterChange}
            />
          </div>

          <div className="form-group">
            <label htmlFor="size">Size</label>
            <select
              id="size"
              name="size"
              value={filters.size || ''}
              onChange={handleFilterChange}
            >
              <option value="">All Sizes</option>
              <option value="XS">XS</option>
              <option value="S">S</option>
              <option value="M">M</option>
              <option value="L">L</option>
              <option value="XL">XL</option>
              <option value="XXL">XXL</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="minPrice">Min Price ($)</label>
            <input
              type="number"
              id="minPrice"
              name="minPrice"
              min="0"
              value={filters.minPrice || ''}
              onChange={handleFilterChange}
            />
          </div>

          <div className="form-group">
            <label htmlFor="maxPrice">Max Price ($)</label>
            <input
              type="number"
              id="maxPrice"
              name="maxPrice"
              min="0"
              value={filters.maxPrice || ''}
              onChange={handleFilterChange}
            />
          </div>

          <button
            className="btn btn-secondary btn-block"
            onClick={() =>
              setFilters({
                category: null,
                color: null,
                size: null,
                minPrice: null,
                maxPrice: null,
              })
            }
          >
            Clear Filters
          </button>
        </aside>

        <main className="products-grid">
          {loading && <div className="alert alert-info">Loading products...</div>}
          {error && <div className="alert alert-danger">{error}</div>}
          {!loading && products.length === 0 && (
            <div className="alert alert-warning">No products found</div>
          )}

          <div className="grid">
            {products.map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
        </main>
      </div>
    </div>
  );
}

function ProductCard({ product }) {
  const [showTryOn, setShowTryOn] = useState(false);

  return (
    <>
      <div className="product-card">
        {product.images && product.images[0] && (
          <div className="product-image">
            <img src={product.images[0]} alt={product.name} />
          </div>
        )}
        <div className="product-info">
          <h3>{product.name}</h3>
          <p className="product-description">{product.description}</p>
          <p className="product-price">${product.price.toFixed(2)}</p>
          {product.style_tags && product.style_tags.length > 0 && (
            <div className="product-tags">
              {product.style_tags.map((tag) => (
                <span key={tag} className="tag">
                  {tag}
                </span>
              ))}
            </div>
          )}
          {product.colors && product.colors.length > 0 && (
            <p className="product-colors">
              <strong>Colors:</strong> {product.colors.join(', ')}
            </p>
          )}
          {product.sizes && product.sizes.length > 0 && (
            <p className="product-sizes">
              <strong>Sizes:</strong> {product.sizes.join(', ')}
            </p>
          )}
          <button 
            className="btn btn-primary btn-block"
            onClick={() => setShowTryOn(true)}
            style={{ marginTop: '0.75rem' }}
          >
            🎨 Try On
          </button>
        </div>
      </div>
      
      <TryOnModal
        isOpen={showTryOn}
        onClose={() => setShowTryOn(false)}
        product={product}
        onSuccess={() => {
          // Optional: show success message
          console.log('Try-on completed successfully');
        }}
      />
    </>
  );
}

export function ProductDetailPage({ productId }) {
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showTryOn, setShowTryOn] = useState(false);

  useEffect(() => {
    loadProduct();
  }, [productId]);

  const loadProduct = async () => {
    try {
      setLoading(true);
      setError('');
      const response = await productsAPI.getById(productId);
      setProduct(response.data);
    } catch (err) {
      setError('Failed to load product');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="alert alert-info">Loading...</div>;
  if (error) return <div className="alert alert-danger">{error}</div>;
  if (!product) return <div className="alert alert-warning">Product not found</div>;

  return (
    <>
      <div className="product-detail">
        <div className="product-detail-image">
          {product.images && product.images[0] && (
            <img src={product.images[0]} alt={product.name} />
          )}
        </div>
        <div className="product-detail-info">
          <h1>{product.name}</h1>
          <p className="product-detail-description">{product.description}</p>
          <p className="product-detail-price">${product.price.toFixed(2)}</p>
          
          {product.colors && product.colors.length > 0 && (
            <div className="detail-section">
              <h3>Available Colors</h3>
              <p>{product.colors.join(', ')}</p>
            </div>
          )}
          
          {product.sizes && product.sizes.length > 0 && (
            <div className="detail-section">
              <h3>Available Sizes</h3>
              <p>{product.sizes.join(', ')}</p>
            </div>
          )}
          
          {product.style_tags && product.style_tags.length > 0 && (
            <div className="detail-section">
              <h3>Style Tags</h3>
              <div className="product-tags">
                {product.style_tags.map((tag) => (
                  <span key={tag} className="tag">
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}
          
          {product.scenarios && product.scenarios.length > 0 && (
            <div className="detail-section">
              <h3>Best For</h3>
              <p>{product.scenarios.join(', ')}</p>
            </div>
          )}
          
          <div className="detail-section">
            <button 
              className="btn btn-primary"
              onClick={() => setShowTryOn(true)}
              style={{ fontSize: '1.1rem', padding: '12px 24px' }}
            >
              🎨 Try This On
            </button>
          </div>
        </div>
      </div>
      
      <TryOnModal
        isOpen={showTryOn}
        onClose={() => setShowTryOn(false)}
        product={product}
        onSuccess={() => {
          console.log('Try-on completed successfully');
        }}
      />
    </>
  );
}

const productsStyles = `
.products-container {
  display: flex;
  gap: 2rem;
  margin-top: 2rem;
}

.filters-sidebar {
  flex: 0 0 250px;
  background: white;
  padding: 1.5rem;
  border-radius: 0.5rem;
  border: 1px solid var(--border);
  height: fit-content;
  position: sticky;
  top: 100px;
}

.filters-sidebar h3 {
  margin-bottom: 1.5rem;
}

.products-grid {
  flex: 1;
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 1.5rem;
}

.product-card {
  background: white;
  border-radius: 0.5rem;
  border: 1px solid var(--border);
  overflow: hidden;
  transition: transform 0.2s, box-shadow 0.2s;
}

.product-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.product-image {
  width: 100%;
  height: 200px;
  overflow: hidden;
  background: var(--light);
}

.product-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.product-info {
  padding: 1rem;
}

.product-info h3 {
  font-size: 1.1rem;
  margin-bottom: 0.5rem;
}

.product-description {
  color: var(--text-secondary);
  font-size: 0.9rem;
  margin-bottom: 0.5rem;
}

.product-price {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--primary);
  margin-bottom: 0.5rem;
}

.product-tags {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin-bottom: 0.5rem;
}

.tag {
  display: inline-block;
  background: var(--light);
  color: var(--text-primary);
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 500;
}

.product-colors,
.product-sizes {
  font-size: 0.9rem;
  color: var(--text-secondary);
  margin-bottom: 0.5rem;
}

.product-detail {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
  margin-top: 2rem;
  background: white;
  padding: 2rem;
  border-radius: 0.5rem;
  border: 1px solid var(--border);
}

.product-detail-image {
  background: var(--light);
  border-radius: 0.5rem;
  overflow: hidden;
}

.product-detail-image img {
  width: 100%;
  height: auto;
}

.product-detail-info h1 {
  margin-bottom: 1rem;
}

.product-detail-description {
  font-size: 1.1rem;
  margin-bottom: 1rem;
  color: var(--text-secondary);
}

.product-detail-price {
  font-size: 2rem;
  font-weight: 600;
  color: var(--primary);
  margin-bottom: 2rem;
}

.detail-section {
  margin-bottom: 2rem;
}

.detail-section h3 {
  margin-bottom: 0.5rem;
}

@media (max-width: 768px) {
  .products-container {
    flex-direction: column;
  }

  .filters-sidebar {
    flex: 1;
    position: static;
  }

  .grid {
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  }

  .product-detail {
    grid-template-columns: 1fr;
  }
}
`;

export const ProductsStyles = () => <style>{productsStyles}</style>;
