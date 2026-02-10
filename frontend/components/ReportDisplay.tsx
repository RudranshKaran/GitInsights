'use client';

import { useState } from 'react';

interface ReportData {
  repo_name: string;
  final_score: number;
  report: {
    summary: string;
    strengths: string[];
    improvements: string[];
    resume_bullets: string[];
  };
  section_scores: {
    documentation: number;
    structure: number;
    configuration: number;
    completeness: number;
  };
}

interface Props {
  report: ReportData;
  onReset: () => void;
}

/**
 * Score Badge Component
 * 
 * Displays the final score visually with appropriate color coding.
 * Accompanies score with neutral context.
 */
function ScoreBadge({ score }: { score: number }) {
  const getScoreClass = () => {
    if (score >= 70) return 'score-badge-excellent';
    if (score >= 50) return 'score-badge-good';
    return 'score-badge-needs-work';
  };

  return (
    <div 
      className={`score-badge ${getScoreClass()}`}
      role="meter"
      aria-valuenow={score}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label={`Readiness score: ${Math.round(score)} out of 100`}
    >
      <span className="score-value">{Math.round(score)}</span>
      <span className="score-label">Readiness Score</span>
    </div>
  );
}

/**
 * Section Scores Component
 * 
 * Displays individual dimension scores with visual progress bars.
 */
function SectionScores({ scores }: { scores: ReportData['section_scores'] }) {
  const scoreItems = [
    { label: 'Documentation', value: scores.documentation },
    { label: 'Structure', value: scores.structure },
    { label: 'Configuration', value: scores.configuration },
    { label: 'Completeness', value: scores.completeness },
  ];

  return (
    <div className="scores-grid">
      {scoreItems.map((item) => (
        <div key={item.label} className="score-item">
          <span className="score-item-label">{item.label}</span>
          <span className="score-item-value">{item.value}/10</span>
          <div className="score-bar">
            <div 
              className="score-bar-fill" 
              style={{ width: `${item.value * 10}%` }}
              aria-hidden="true"
            />
          </div>
        </div>
      ))}
    </div>
  );
}

/**
 * Copy Button Component
 * 
 * Enables easy copying of resume bullets with feedback.
 */
function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback for older browsers
      const textarea = document.createElement('textarea');
      textarea.value = text;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <button
      onClick={handleCopy}
      className={`copy-btn ${copied ? 'copy-btn-copied' : ''}`}
      aria-label={copied ? 'Copied!' : 'Copy to clipboard'}
    >
      {copied ? '✓ Copied' : 'Copy'}
    </button>
  );
}

/**
 * Report Display Component
 * 
 * Renders the complete evaluation report in clearly separated sections.
 * Uses headings and bullet lists for scannability.
 * Ensures resume bullets are easily copyable.
 */
export function ReportDisplay({ report, onReset }: Props) {
  return (
    <article className="report" aria-label="Repository evaluation report">
      {/* Header with score */}
      <header className="report-header">
        <h1 className="report-title">{report.repo_name}</h1>
        <ScoreBadge score={report.final_score} />
      </header>

      {/* Project Summary */}
      <section className="report-section" aria-labelledby="summary-heading">
        <h2 id="summary-heading" className="section-title">
          📋 Project Summary
        </h2>
        <div className="section-content">
          <p className="summary-text">{report.report.summary}</p>
        </div>
      </section>

      {/* Strengths */}
      {report.report.strengths.length > 0 && (
        <section className="report-section" aria-labelledby="strengths-heading">
          <h2 id="strengths-heading" className="section-title">
            ✅ Strengths
          </h2>
          <div className="section-content">
            <ul className="section-list">
              {report.report.strengths.map((strength, index) => (
                <li key={index}>{strength}</li>
              ))}
            </ul>
          </div>
        </section>
      )}

      {/* Areas for Improvement */}
      {report.report.improvements.length > 0 && (
        <section className="report-section" aria-labelledby="improvements-heading">
          <h2 id="improvements-heading" className="section-title">
            📈 Areas for Improvement
          </h2>
          <div className="section-content">
            <ul className="section-list">
              {report.report.improvements.map((improvement, index) => (
                <li key={index}>{improvement}</li>
              ))}
            </ul>
          </div>
        </section>
      )}

      {/* Resume-Ready Bullet Points */}
      {report.report.resume_bullets.length > 0 && (
        <section className="report-section" aria-labelledby="resume-heading">
          <h2 id="resume-heading" className="section-title">
            📝 Resume-Ready Bullet Points
          </h2>
          <div className="section-content">
            <ul className="section-list">
              {report.report.resume_bullets.map((bullet, index) => (
                <li key={index}>
                  <div className="resume-bullet-item">
                    <span className="resume-bullet-text">{bullet}</span>
                    <CopyButton text={bullet} />
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </section>
      )}

      {/* Detailed Scores */}
      <section className="report-section" aria-labelledby="scores-heading">
        <h2 id="scores-heading" className="section-title">
          📊 Detailed Scores
        </h2>
        <div className="section-content">
          <SectionScores scores={report.section_scores} />
        </div>
      </section>

      {/* Actions */}
      <div className="report-actions">
        <button onClick={onReset} className="btn btn-primary btn-lg">
          Analyze Another Repository
        </button>
      </div>
    </article>
  );
}
