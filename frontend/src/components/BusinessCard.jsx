import { useState } from "react";

const VERDICT_STYLES = {
  Verified: { label: "VERIFIED", className: "badge badge-verified" },
  "Contradiction Found": { label: "CONTRADICTION", className: "badge badge-contradiction" },
  "Insufficient Evidence": { label: "INSUFFICIENT EVIDENCE", className: "badge badge-insufficient" },
  Likely: { label: "LIKELY", className: "badge badge-likely" },
};

const SOURCE_RELIABILITY = {
  npi_registry: 0.95,
  official_website: 0.85,
  google_maps: 0.75,
  linkedin: 0.65,
  yellow_pages: 0.50,
  duckduckgo: 0.40,
};

function ConfidenceFormula({ claim }) {
  const sources = [...new Set(claim.evidence.map((e) => e.source))];
  if (sources.length < 2) return null;
  const weights = sources.map((s) => SOURCE_RELIABILITY[s] || 0.35);
  const product = weights.reduce((acc, w) => acc * (1 - w), 1);
  const confidence = ((1 - product) * 100).toFixed(1);
  const formula = weights.map((w) => `(1-${w})`).join(" × ");
  return (
    <div className="formula-box">
      <div className="formula-title">Confidence Formula</div>
      <div className="formula-math">1 - {formula} = <strong>{confidence}%</strong></div>
    </div>
  );
}

function WhyVerified({ business }) {
  const verifiedClaims = business.claims.filter((c) => c.verdict === "Verified" || c.confidence >= 0.85);
  if (verifiedClaims.length === 0) return null;

  return (
    <div className="why-verified">
      <div className="why-title">✓ Why Verified?</div>
      {verifiedClaims.map((claim, i) => {
        const sources = [...new Set(claim.evidence.map((e) => e.source))];
        return (
          <div className="verified-claim" key={i}>
            <div className="verified-field">{claim.field}: <span className="verified-value">{claim.value}</span></div>
            <div className="verified-sources">
              {sources.map((s) => (
                <span key={s} className="source-tag">{s}</span>
              ))}
            </div>
          </div>
        );
      })}
      {verifiedClaims[0] && <ConfidenceFormula claim={verifiedClaims[0]} />}
    </div>
  );
}

export default function BusinessCard({ business }) {
  const [expanded, setExpanded] = useState(false);

  const overall =
    business.claims.find((c) => c.verdict === "Contradiction Found") ||
    business.claims.find((c) => c.verdict === "Verified") ||
    business.claims[0];
  const style = VERDICT_STYLES[overall?.verdict] || VERDICT_STYLES["Insufficient Evidence"];
  const isVerified = overall?.verdict === "Verified";

  return (
    <div className={`business-card ${isVerified ? "card-verified" : ""}`}>
      <div className="card-header">
        <span className="business-name">{business.business_name}</span>
        <span className={style.className}>{style.label}</span>
      </div>

      {isVerified && <WhyVerified business={business} />}

      <div className="claims-toggle" onClick={() => setExpanded(!expanded)}>
        {expanded ? "▲ Hide details" : "▼ Show all claims"}
      </div>

      {expanded && business.claims.map((claim, i) => (
        <div className="claim-row" key={i}>
          <b>{claim.field}:</b> {claim.value} &nbsp;
          Confidence: {(claim.confidence * 100).toFixed(0)}% &nbsp;
          Evidence: {claim.evidence.map((e) => e.source).join(", ")}
          {claim.escalated && (
            <div className="escalation-note">→ Escalated: checked {claim.escalation_source_checked}</div>
          )}
        </div>
      ))}
    </div>
  );
}