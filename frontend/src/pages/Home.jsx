import React from 'react';
import { Link } from 'react-router-dom';
import '../styles/home.css';

export function HomePage() {
  return (
    <div className="home">
      <section className="hero">
        <div className="hero-content">
          <h1>👗 Fashion AI Stylist</h1>
          <p>Get personalized outfit recommendations powered by AI</p>
          <div className="hero-buttons">
            <Link to="/outfit" className="btn btn-primary btn-lg">
              Generate Outfit
            </Link>
            <Link to="/products" className="btn btn-outline btn-lg">
              Browse Shop
            </Link>
          </div>
        </div>
      </section>

      <section className="features">
        <h2>Why Choose Fashion AI?</h2>
        <div className="features-grid">
          <FeatureCard
            icon="🤖"
            title="AI-Powered Recommendations"
            description="Get smart outfit suggestions based on your style preferences and available inventory."
          />
          <FeatureCard
            icon="🎨"
            title="Style Matching"
            description="Our AI understands color compatibility, style harmony, and occasion-specific recommendations."
          />
          <FeatureCard
            icon="🛍️"
            title="Curated Catalog"
            description="Browse a carefully selected collection of fashion items from various categories."
          />
          <FeatureCard
            icon="💰"
            title="Smart Pricing"
            description="Get complete outfit bundles with transparent pricing for the entire look."
          />
        </div>
      </section>

      <section className="how-it-works">
        <h2>How It Works</h2>
        <div className="steps">
          <Step number="1" title="Choose Your Style" description="Select casual, formal, sport, or office style" />
          <Step number="2" title="Pick a Scenario" description="Tell us the occasion - work, date, gym, etc." />
          <Step number="3" title="Set Preferences" description="Choose your sizes and preferred colors" />
          <Step number="4" title="Get Recommendations" description="AI generates a complete outfit with explanation" />
        </div>
      </section>

      <section className="cta">
        <h2>Ready to Transform Your Style?</h2>
        <p>Start getting AI-powered outfit recommendations today</p>
        <Link to="/outfit" className="btn btn-primary btn-lg">
          Create Your First Outfit
        </Link>
      </section>
    </div>
  );
}

function FeatureCard({ icon, title, description }) {
  return (
    <div className="feature-card">
      <div className="feature-icon">{icon}</div>
      <h3>{title}</h3>
      <p>{description}</p>
    </div>
  );
}

function Step({ number, title, description }) {
  return (
    <div className="step">
      <div className="step-number">{number}</div>
      <h3>{title}</h3>
      <p>{description}</p>
    </div>
  );
}
