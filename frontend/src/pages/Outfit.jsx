import React, { useState, useEffect } from 'react';
import { outfitAPI } from '../services/api';
import { useForm } from '../hooks';

export function OutfitGeneratorPage() {
  const [outfits, setOutfits] = useState([]);
  const [selectedOutfit, setSelectedOutfit] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    loadOutfitHistory();
  }, []);

  const loadOutfitHistory = async () => {
    try {
      const response = await outfitAPI.history();
      setOutfits(response.data);
    } catch (err) {
      console.error('Failed to load outfit history:', err);
    }
  };

  const form = useForm(
    { style: 'casual', scenario: 'everyday', sizes: [], colors: [] },
    async (values) => {
      try {
        setLoading(true);
        setError('');
        const response = await outfitAPI.generate(
          values.style,
          values.scenario,
          values.sizes,
          values.colors
        );
        setSelectedOutfit(response.data);
        loadOutfitHistory();
      } catch (err) {
        const message = err.response?.data?.detail || 'Failed to generate outfit';
        setError(message);
      } finally {
        setLoading(false);
      }
    }
  );

  const handleSizeChange = (e) => {
    const { value, checked } = e.target;
    if (checked) {
      form.setValues((prev) => ({
        ...prev,
        sizes: [...prev.sizes, value],
      }));
    } else {
      form.setValues((prev) => ({
        ...prev,
        sizes: prev.sizes.filter((s) => s !== value),
      }));
    }
  };

  const handleColorChange = (e) => {
    const value = e.target.value.trim();
    if (value) {
      form.setValues((prev) => ({
        ...prev,
        colors: [...prev.colors, value],
      }));
      e.target.value = '';
    }
  };

  const removeColor = (colorToRemove) => {
    form.setValues((prev) => ({
      ...prev,
      colors: prev.colors.filter((c) => c !== colorToRemove),
    }));
  };

  return (
    <div>
      <h1>Outfit Generator</h1>

      <div className="outfit-generator-container">
        <aside className="generator-form-sidebar lux-card">
          <h2>Create Outfit</h2>
          {error && <div className="alert alert-danger">{error}</div>}

          <form onSubmit={form.handleSubmit}>
            <div className="form-group">
              <label htmlFor="style">Style</label>
              <select
                id="style"
                name="style"
                value={form.values.style}
                onChange={form.handleChange}
              >
                <option value="casual">Casual</option>
                <option value="formal">Formal</option>
                <option value="sport">Sport</option>
                <option value="office">Office</option>
                <option value="party">Party</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="scenario">Scenario</label>
              <select
                id="scenario"
                name="scenario"
                value={form.values.scenario}
                onChange={form.handleChange}
              >
                <option value="everyday">Everyday</option>
                <option value="weekend">Weekend</option>
                <option value="work">Work</option>
                <option value="date">Date</option>
                <option value="gym">Gym</option>
                <option value="vacation">Vacation</option>
              </select>
            </div>

            <div className="form-group">
              <label>Sizes</label>
              <div className="checkbox-group">
                {['XS', 'S', 'M', 'L', 'XL', 'XXL'].map((size) => (
                  <label key={size} className="checkbox-label">
                    <input
                      type="checkbox"
                      value={size}
                      checked={form.values.sizes.includes(size)}
                      onChange={handleSizeChange}
                    />
                    {size}
                  </label>
                ))}
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="colorInput">Colors (press Enter to add)</label>
              <input
                type="text"
                id="colorInput"
                placeholder="e.g., blue, red, black"
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    handleColorChange(e);
                  }
                }}
              />
              {form.values.colors.length > 0 && (
                <div className="color-tags">
                  {form.values.colors.map((color) => (
                    <span key={color} className="color-tag">
                      {color}
                      <button
                        type="button"
                        onClick={() => removeColor(color)}
                        className="color-tag-remove"
                      >
                        ×
                      </button>
                    </span>
                  ))}
                </div>
              )}
            </div>

            <button
              type="submit"
              className="btn btn-primary btn-block btn-lg"
              disabled={loading || form.values.sizes.length === 0}
            >
              {loading ? 'Generating...' : 'Generate Outfit'}
            </button>
          </form>
        </aside>

        <main className="outfit-results">
          {selectedOutfit && <OutfitResult outfit={selectedOutfit} />}

          {outfits.length > 0 && (
            <div className="outfit-history">
              <h2>History</h2>
              <div className="history-list">
                {outfits.map((outfit, index) => (
                  <div
                    key={index}
                    className="history-item"
                    onClick={() => setSelectedOutfit(outfit)}
                  >
                    <h4>Outfit #{index + 1}</h4>
                    <p className="history-item-meta">
                      Items: {outfit.outfit ? Object.keys(outfit.outfit).length : 0}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

function OutfitResult({ outfit }) {
  const { outfit: items, ai_explanation: explanation, total_price: totalPrice } = outfit;

  return (
    <div className="outfit-result">
      <h2>Your Generated Outfit</h2>

      <div className="outfit-items">
        {items?.top && <OutfitItem item={items.top} slot="TOP" />}
        {items?.bottom && <OutfitItem item={items.bottom} slot="BOTTOM" />}
        {items?.shoes && <OutfitItem item={items.shoes} slot="SHOES" />}
        {items?.accessory && <OutfitItem item={items.accessory} slot="ACCESSORY" />}
      </div>

      <div className="outfit-summary">
        <h3>Total Price</h3>
        <p className="total-price">${totalPrice?.toFixed(2) || '0.00'}</p>
      </div>

      {explanation && (
        <div className="outfit-explanation">
          <h3>AI Explanation</h3>
          <p className="explanation-text">{explanation}</p>
        </div>
      )}
    </div>
  );
}

function OutfitItem({ item, slot }) {
  return (
    <div className="outfit-item">
      <h4>{slot}</h4>
      {item.image && (
        <div className="item-image">
          <img src={item.image} alt={item.name} />
        </div>
      )}
      <div className="item-info">
        <p className="item-name">{item.name}</p>
        <p className="item-price">${item.price?.toFixed(2) || '0.00'}</p>
      </div>
    </div>
  );
}

const outfitStyles = `
.outfit-generator-container {
  display: grid;
  grid-template-columns: 360px 1fr;
  gap: 1rem;
  margin-top: 2rem;
}

.generator-form-sidebar {
  padding: 1.2rem;
  height: fit-content;
  position: sticky;
  top: 100px;
}

.generator-form-sidebar h2 {
  margin-bottom: 1.5rem;
}

.checkbox-group {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.5rem;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  font-weight: normal;
  margin: 0;
}

.checkbox-label input[type="checkbox"] {
  cursor: pointer;
  width: auto;
  accent-color: var(--gold);
}

.color-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.color-tag {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  background: #101010;
  border: 1px solid var(--border);
  color: var(--muted);
  padding: 0.38rem 0.6rem;
  font-size: 0.9rem;
}

.color-tag-remove {
  background: none;
  border: none;
  color: var(--muted);
  cursor: pointer;
  font-size: 1.2rem;
  padding: 0;
  line-height: 1;
}

.outfit-results {
  flex: 1;
}

.outfit-result {
  background: var(--card);
  border: 1px solid var(--border);
  padding: 1.2rem;
  border: 1px solid var(--border);
  margin-bottom: 2rem;
  animation: fadeInUp 0.6s ease forwards;
}

.outfit-result h2 {
  margin-bottom: 1.5rem;
}

.outfit-items {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.outfit-item {
  background: #101010;
  padding: 1rem;
  border: 1px solid var(--border);
  text-align: center;
  transition: transform 0.3s ease, border-color 0.3s ease;
}

.outfit-item:hover {
  transform: translateY(-4px);
  border-color: var(--gold);
}

.outfit-item h4 {
  color: var(--gold);
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  margin-bottom: 0.5rem;
}

.item-image {
  width: 100%;
  height: 150px;
  background: #0d0d0d;
  overflow: hidden;
  margin-bottom: 0.75rem;
}

.item-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.item-name {
  font-weight: 500;
  margin-bottom: 0.25rem;
}

.item-price {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--gold);
}

.outfit-summary {
  background: #101010;
  border: 1px solid var(--border);
  padding: 1.5rem;
  margin-bottom: 2rem;
}

.outfit-summary h3 {
  margin-bottom: 0.5rem;
}

.total-price {
  font-size: 2.3rem;
  font-weight: 600;
  color: var(--gold);
  margin: 0;
}

.outfit-explanation {
  background: #101010;
  padding: 1.5rem;
  border-left: 3px solid var(--gold);
}

.outfit-explanation h3 {
  margin-bottom: 1rem;
}

.explanation-text {
  line-height: 1.8;
  color: var(--muted);
  font-style: italic;
}

.outfit-history {
  background: var(--card);
  padding: 1.2rem;
  border: 1px solid var(--border);
}

.outfit-history h2 {
  margin-bottom: 1.5rem;
}

.history-list {
  display: grid;
  gap: 0.75rem;
}

.history-item {
  background: #101010;
  padding: 1rem;
  border: 1px solid var(--border);
  cursor: pointer;
  transition: transform 0.3s ease, border-color 0.3s ease;
}

.history-item:hover {
  transform: translateY(-4px);
  border-color: var(--gold);
}

.history-item h4 {
  margin-bottom: 0.25rem;
}

.history-item-meta {
  font-size: 0.875rem;
  color: var(--muted);
  margin: 0;
}

@media (max-width: 1024px) {
  .outfit-generator-container {
    grid-template-columns: 1fr;
  }

  .generator-form-sidebar {
    position: static;
  }
}

@media (max-width: 768px) {
  .outfit-items {
    grid-template-columns: repeat(2, 1fr);
  }

  .checkbox-group {
    grid-template-columns: repeat(2, 1fr);
  }
}
`;

export const OutfitStyles = () => <style>{outfitStyles}</style>;
