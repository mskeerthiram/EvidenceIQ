import BusinessCard from "./BusinessCard.jsx";

export default function ResultsScreen({ query, businesses, stats, summaryText, onNewSearch }) {
  return (
    <div className="screen results-screen">
      <button className="back-link" onClick={onNewSearch}>
        &larr; New search
      </button>
      <h2>{query}</h2>

      <div className="summary-bar">
        Found: {stats.found} &nbsp;|&nbsp; Verified: {stats.verified} &nbsp;|&nbsp; Conflicts: {stats.conflicts}{" "}
        &nbsp;|&nbsp; Sources: {stats.sources} &nbsp;|&nbsp; Time: {stats.time}s
      </div>

      {businesses.map((b) => (
        <BusinessCard key={b.business_id} business={b} />
      ))}

      {businesses.length === 0 && <p className="loading-note">Investigating&hellip;</p>}

      {summaryText && (
        <div className="research-summary">
          <h3>Research Summary</h3>
          <p>{summaryText}</p>
        </div>
      )}
    </div>
  );
}
