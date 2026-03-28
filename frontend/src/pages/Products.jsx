import React, { useState, useEffect, useMemo } from 'react';
import { useParams } from 'react-router-dom';
import { productsAPI, categoriesAPI } from '../services/api';
import TryOnModal from '../components/TryOnModal';

const PLACEHOLDER_IMAGE = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='600' height='800'%3E%3Crect width='100%25' height='100%25' fill='%23101010'/%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' fill='%23a0a0a0' font-family='Arial' font-size='26'%3ENO IMAGE%3C/text%3E%3C/svg%3E";

export function ProductsPage() {
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [filters, setFilters] = useState({
    category: null,
    brand: null,
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

  const displayProducts = useMemo(() => {
    if (!filters.brand) return products;
    const brandFilter = filters.brand.toLowerCase();
    return products.filter((p) => {
      const brand = (p.brand || p.name?.split(' ')[0] || 'Maison').toLowerCase();
      return brand.includes(brandFilter);
    });
  }, [products, filters.brand]);

  const brandOptions = useMemo(() => {
    const brands = products.map((p) => p.brand || p.name?.split(' ')[0] || 'Maison');
    return Array.from(new Set(brands));
  }, [products]);

  return (
    <div>
      <h1>Shop</h1>

      <div className="products-container">
        <aside className="filters-sidebar lux-card">
          <h3>Filters</h3>

          <div className="form-group">
            <label htmlFor="categoryId">Style</label>
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
            <label htmlFor="brand">Brand</label>
            <select
              id="brand"
              name="brand"
              value={filters.brand || ''}
              onChange={handleFilterChange}
            >
              <option value="">All Brands</option>
              {brandOptions.map((brand) => (
                <option key={brand} value={brand}>{brand}</option>
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
            <label htmlFor="minPrice">Min Price</label>
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
            <label htmlFor="maxPrice">Max Price</label>
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
                brand: null,
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
          {!loading && displayProducts.length === 0 && (
            <div className="alert alert-warning">No products found</div>
          )}

          <div className="grid">
            {displayProducts.map((product) => (
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
  const brand = (product.brand || product.name?.split(' ')[0] || 'Maison').toUpperCase();
  const image = product.images?.[0] || PLACEHOLDER_IMAGE;

  return (
    <>
      <div className="product-card lux-card">
        <div className="product-image">
          <img src={image} alt={product.name} />
          <button
            className="btn btn-primary product-hover-btn"
            onClick={() => setShowTryOn(true)}
          >
            Try On
          </button>
        </div>
        <div className="product-info">
          <p className="product-brand">{brand}</p>
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

export function ProductDetailPage() {
  const { id } = useParams();
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showTryOn, setShowTryOn] = useState(false);

  useEffect(() => {
    loadProduct();
  }, [id]);

  const loadProduct = async () => {
    try {
      setLoading(true);
      setError('');
      const response = await productsAPI.getById(id);
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
          <img src={product.images?.[0] || PLACEHOLDER_IMAGE} alt={product.name} />
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
  display: grid;
  grid-template-columns: 1fr;
  gap: 1.4rem;
  margin-top: 2rem;
}

.filters-sidebar {
  display: grid;
  grid-template-columns: repeat(5, minmax(140px, 1fr));
  gap: 1rem;
  padding: 1.2rem;
  position: sticky;
  top: 100px;
  z-index: 4;
}

.filters-sidebar h3 {
  grid-column: 1 / -1;
  margin-bottom: 0.3rem;
}

.products-grid {
  flex: 1;
}

.grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1rem;
}

.product-card {
  overflow: hidden;
}

.product-image {
  position: relative;
  width: 100%;
  aspect-ratio: 3 / 4;
  overflow: hidden;
  background: #0d0d0d;
}

.product-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.product-hover-btn {
  position: absolute;
  left: 50%;
  bottom: 14px;
  transform: translateX(-50%);
  opacity: 0;
  pointer-events: none;
}

.product-card:hover .product-hover-btn {
  opacity: 1;
  pointer-events: auto;
}

.product-info {
  padding: 0.9rem;
}

.product-info h3 {
  font-size: 0.92rem;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  margin-bottom: 0.5rem;
}

.product-brand {
  color: var(--gold);
  margin-bottom: 0.35rem;
  font-size: 0.67rem;
  letter-spacing: 0.09em;
  text-transform: uppercase;
}

.product-description {
  color: var(--muted);
  font-size: 0.82rem;
  margin-bottom: 0.5rem;
}

.product-price {
  font-size: 1.2rem;
  font-weight: 600;
  color: var(--gold);
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
  background: #101010;
  color: var(--muted);
  padding: 0.25rem 0.75rem;
  border: 1px solid var(--border);
  font-size: 0.75rem;
  font-weight: 500;
}

.product-colors,
.product-sizes {
  font-size: 0.9rem;
  color: var(--muted);
  margin-bottom: 0.5rem;
}

.product-detail {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
  margin-top: 2rem;
  padding: 2rem;
  background: var(--card);
  border: 1px solid var(--border);
}

.product-detail-image {
  background: #0d0d0d;
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
  color: var(--muted);
}

.product-detail-price {
  font-size: 2rem;
  font-weight: 600;
  color: var(--gold);
  margin-bottom: 2rem;
}

.detail-section {
  margin-bottom: 2rem;
}

.detail-section h3 {
  margin-bottom: 0.5rem;
}

@media (max-width: 768px) {
  .filters-sidebar {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    position: static;
  }

  .grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .product-detail {
    grid-template-columns: 1fr;
  }
}
`;

export const ProductsStyles = () => <style>{productsStyles}</style>;
