import React from 'react';
import { Link } from 'react-router-dom';
import '../styles/home.css';

export function HomePage() {
  return (
    <div className="home">
      <section className="hero-fullscreen">
        <div className="hero-overlay" />
        <div className="hero-content fade-in-up">
          <h1>DISCOVER YOUR STYLE</h1>
          <p className="hero-subheading">AI-curated premium looks for modern fashion experience.</p>
          <div className="hero-buttons">
            <Link to="/products" className="btn btn-primary btn-lg">
              Explore Collection
            </Link>
            <Link to="/outfit" className="btn btn-outline btn-lg">
              Try AI Stylist
            </Link>
          </div>
        </div>
      </section>

      <section className="features">
        <h2>Luxury AI Experience</h2>
        <div className="steps">
          <Step number="01" title="Personal Styling" description="Select style and occasion, get instant recommendations." />
          <Step number="02" title="Virtual Try-On" description="Upload your photo and preview premium looks." />
          <Step number="03" title="Curated Selection" description="Explore catalog with AI-powered fit suggestions." />
          <Step number="04" title="Premium Output" description="Get complete outfit with explanation and total price." />
        </div>
      </section>
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
