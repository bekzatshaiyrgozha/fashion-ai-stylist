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
      <h1>🎨 Outfit Generator</h1>

      <div className="outfit-generator-container">
        <aside className="generator-form-sidebar">
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
              <label htmlFor="colorInput">Colors (add and press Enter)</label>
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
      <h2>✨ Your Generated Outfit</h2>

      <div className="outfit-items">
        {items?.top && <OutfitItem item={items.top} slot="Top" />}
        {items?.bottom && <OutfitItem item={items.bottom} slot="Bottom" />}
        {items?.shoes && <OutfitItem item={items.shoes} slot="Shoes" />}
        {items?.accessory && <OutfitItem item={items.accessory} slot="Accessory" />}
      </div>

      <div className="outfit-summary">
        <h3>💰 Total Price</h3>
        <p className="total-price">${totalPrice?.toFixed(2) || '0.00'}</p>
      </div>

      {explanation && (
        <div className="outfit-explanation">
          <h3>🤖 AI Stylist Explanation</h3>
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
  display: flex;
  gap: 2rem;
  margin-top: 2rem;
}

.generator-form-sidebar {
  flex: 0 0 350px;
  background: white;
  padding: 2rem;
  border-radius: 0.5rem;
  border: 1px solid var(--border);
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
  background: var(--primary);
  color: white;
  padding: 0.5rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.9rem;
}

.color-tag-remove {
  background: none;
  border: none;
  color: white;
  cursor: pointer;
  font-size: 1.2rem;
  padding: 0;
  line-height: 1;
}

.outfit-results {
  flex: 1;
}

.outfit-result {
  background: white;
  padding: 2rem;
  border-radius: 0.5rem;
  border: 1px solid var(--border);
  margin-bottom: 2rem;
}

.outfit-result h2 {
  margin-bottom: 1.5rem;
}

.outfit-items {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.outfit-item {
  background: var(--light);
  padding: 1rem;
  border-radius: 0.5rem;
  border: 2px solid var(--border);
  text-align: center;
}

.outfit-item h4 {
  color: var(--text-secondary);
  font-size: 0.9rem;
  text-transform: uppercase;
  margin-bottom: 0.5rem;
}

.item-image {
  width: 100%;
  height: 150px;
  background: white;
  border-radius: 0.375rem;
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
  color: var(--primary);
}

.outfit-summary {
  background: var(--light);
  padding: 1.5rem;
  border-radius: 0.5rem;
  margin-bottom: 2rem;
}

.outfit-summary h3 {
  margin-bottom: 0.5rem;
}

.total-price {
  font-size: 2rem;
  font-weight: 600;
  color: var(--primary);
  margin: 0;
}

.outfit-explanation {
  background: var(--light);
  padding: 1.5rem;
  border-radius: 0.5rem;
  border-left: 4px solid var(--secondary);
}

.outfit-explanation h3 {
  margin-bottom: 1rem;
}

.explanation-text {
  line-height: 1.8;
  color: var(--text-primary);
}

.outfit-history {
  background: white;
  padding: 2rem;
  border-radius: 0.5rem;
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
  background: var(--light);
  padding: 1rem;
  border-radius: 0.375rem;
  border: 1px solid var(--border);
  cursor: pointer;
  transition: all 0.2s;
}

.history-item:hover {
  background: white;
  border-color: var(--primary);
}

.history-item h4 {
  margin-bottom: 0.25rem;
}

.history-item-meta {
  font-size: 0.875rem;
  color: var(--text-secondary);
  margin: 0;
}

@media (max-width: 1024px) {
  .outfit-generator-container {
    flex-direction: column;
  }

  .generator-form-sidebar {
    flex: 1;
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
