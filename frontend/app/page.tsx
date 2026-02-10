'use client';

import Link from 'next/link';

/**
 * Landing Page Component
 * 
 * Premium SaaS landing page for GitInsight.
 * Features animated hero, trust stats, feature cards, and CTAs.
 */
export default function LandingPage() {
  return (
    <div className="landing-page">
      <main className="landing-main">
        {/* Hero Section */}
        <section className="landing-hero">
          <div className="landing-hero-badge">
            <span className="landing-hero-badge-dot"></span>
            <span>Free to use • No sign up required</span>
          </div>
          
          <h1 className="landing-hero-title">
            Unlock the Power<br />of Your Code
          </h1>
          
          <p className="landing-hero-tagline">
            AI-Powered GitHub Repository Analysis
          </p>
          
          <p className="landing-hero-description">
            Transform any GitHub repository into actionable insights. Get instant quality scores, 
            recruiter-ready resume bullets, and concrete improvement recommendations—all powered by AI.
          </p>
          
          <div className="landing-cta-group">
            <Link href="/analyze" className="landing-cta">
              <span>Analyze Your Repository</span>
              <span aria-hidden="true">→</span>
            </Link>
            <a href="#how-it-works" className="landing-cta-secondary">
              <span>See How It Works</span>
            </a>
          </div>
        </section>

        {/* Trust Stats */}
        <section className="landing-trust">
          <p className="trust-label">Trusted by developers worldwide</p>
          <div className="trust-stats">
            <div className="trust-stat">
              <div className="trust-stat-value">10+</div>
              <div className="trust-stat-label">Metrics Analyzed</div>
            </div>
            <div className="trust-stat">
              <div className="trust-stat-value">AI</div>
              <div className="trust-stat-label">Powered Insights</div>
            </div>
            <div className="trust-stat">
              <div className="trust-stat-value">100%</div>
              <div className="trust-stat-label">Free Forever</div>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section className="landing-features">
          <div className="landing-section-header">
            <span className="landing-section-label">Features</span>
            <h2 className="landing-section-title">Everything You Need to Shine</h2>
            <p className="landing-section-subtitle">
              Comprehensive analysis that helps you understand your code's strengths 
              and areas for improvement—all in one beautifully designed report.
            </p>
          </div>
          
          <div className="features-grid">
            <div className="feature-card">
              <div className="feature-icon" aria-hidden="true">📊</div>
              <h3 className="feature-title">Quality Scoring</h3>
              <p className="feature-description">
                Get detailed scores across documentation, structure, configuration, 
                and completeness. Know exactly where your project excels.
              </p>
            </div>
            <div className="feature-card">
              <div className="feature-icon" aria-hidden="true">🎯</div>
              <h3 className="feature-title">Tech Stack Detection</h3>
              <p className="feature-description">
                Automatically identify languages, frameworks, and tools in your 
                repository with intelligent analysis.
              </p>
            </div>
            <div className="feature-card">
              <div className="feature-icon" aria-hidden="true">💡</div>
              <h3 className="feature-title">Smart Recommendations</h3>
              <p className="feature-description">
                Receive actionable, prioritized suggestions tailored to your 
                specific project to maximize impact.
              </p>
            </div>
            <div className="feature-card">
              <div className="feature-icon" aria-hidden="true">📝</div>
              <h3 className="feature-title">Resume Bullets</h3>
              <p className="feature-description">
                Generate polished, STAR-formatted bullet points that highlight 
                your achievements—copy directly to your resume.
              </p>
            </div>
            <div className="feature-card">
              <div className="feature-icon" aria-hidden="true">🔍</div>
              <h3 className="feature-title">Deep Code Analysis</h3>
              <p className="feature-description">
                Our AI examines code clarity, patterns, and maintainability 
                to provide comprehensive feedback.
              </p>
            </div>
            <div className="feature-card">
              <div className="feature-icon" aria-hidden="true">⚡</div>
              <h3 className="feature-title">Instant Results</h3>
              <p className="feature-description">
                No waiting around—get your complete analysis in seconds, 
                not hours. Fast feedback when you need it.
              </p>
            </div>
          </div>
        </section>

        {/* How It Works */}
        <section className="landing-how-it-works" id="how-it-works">
          <div className="landing-section-header">
            <span className="landing-section-label">How It Works</span>
            <h2 className="landing-section-title">Three Simple Steps</h2>
            <p className="landing-section-subtitle">
              From repository URL to comprehensive insights in under a minute.
            </p>
          </div>
          
          <div className="steps-container">
            <div className="step-item">
              <div className="step-number">1</div>
              <h3 className="step-title">Paste Your URL</h3>
              <p className="step-description">
                Enter any public GitHub repository URL—personal projects, 
                coursework, or open source contributions.
              </p>
            </div>
            <div className="step-item">
              <div className="step-number">2</div>
              <h3 className="step-title">AI Analysis</h3>
              <p className="step-description">
                Our AI examines your code, documentation, structure, and 
                patterns to generate comprehensive insights.
              </p>
            </div>
            <div className="step-item">
              <div className="step-number">3</div>
              <h3 className="step-title">Get Your Report</h3>
              <p className="step-description">
                View detailed scores, resume bullets, and actionable 
                recommendations to level up your project.
              </p>
            </div>
          </div>
        </section>

        {/* Who It's For */}
        <section className="landing-audience">
          <div className="landing-section-header">
            <span className="landing-section-label">Who It's For</span>
            <h2 className="landing-section-title">Built for Ambitious Developers</h2>
            <p className="landing-section-subtitle">
              Whether you're job hunting, learning, or leading a team—GitInsight helps you shine.
            </p>
          </div>
          
          <div className="audience-grid">
            <div className="audience-item">
              <span className="audience-icon" aria-hidden="true">👩‍💻</span>
              <p className="audience-label">Job Seekers</p>
              <p className="audience-description">
                Stand out with polished resume bullets
              </p>
            </div>
            <div className="audience-item">
              <span className="audience-icon" aria-hidden="true">🎓</span>
              <p className="audience-label">Students</p>
              <p className="audience-description">
                Improve projects before submission
              </p>
            </div>
            <div className="audience-item">
              <span className="audience-icon" aria-hidden="true">🚀</span>
              <p className="audience-label">Open Source</p>
              <p className="audience-description">
                Ensure quality for contributors
              </p>
            </div>
            <div className="audience-item">
              <span className="audience-icon" aria-hidden="true">👥</span>
              <p className="audience-label">Team Leads</p>
              <p className="audience-description">
                Quick quality assessments at scale
              </p>
            </div>
          </div>
        </section>

        {/* Final CTA */}
        <section className="landing-cta-section">
          <div className="cta-box">
            <h2 className="cta-title">Ready to Analyze Your Code?</h2>
            <p className="cta-description">
              Join developers who use GitInsight to improve their projects 
              and showcase their work professionally.
            </p>
            <Link href="/analyze" className="landing-cta">
              <span>Get Started — It's Free</span>
              <span aria-hidden="true">→</span>
            </Link>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="landing-footer">
        <div className="footer-content">
          <span className="footer-logo">GitInsight</span>
          <p className="footer-text">
            AI-powered GitHub repository analysis • Made with ❤️ for developers
          </p>
          <div className="footer-links">
            <a href="https://github.com" className="footer-link" target="_blank" rel="noopener noreferrer">
              GitHub
            </a>
            <Link href="/analyze" className="footer-link">
              Analyze
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
