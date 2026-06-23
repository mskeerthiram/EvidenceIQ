import { useRef, useState } from "react";
import SearchScreen from "./components/SearchScreen.jsx";
import ResultsScreen from "./components/ResultsScreen.jsx";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

export default function App() {
  const [stage, setStage] = useState("search"); // "search" | "results"
  const [businesses, setBusinesses] = useState([]);
  const [stats, setStats] = useState({ found: 0, verified: 0, conflicts: 0, sources: 0, time: 0 });
  const [summaryText, setSummaryText] = useState("");
  const [query, setQuery] = useState("");
  const sourceRef = useRef(null);

  function runSearch(q) {
    setQuery(q);
    setBusinesses([]);
    setStats({ found: 0, verified: 0, conflicts: 0, sources: 0, time: 0 });
    setSummaryText("");
    setStage("results");

    if (sourceRef.current) sourceRef.current.close();

    const es = new EventSource(`${API_BASE}/api/search/stream?query=${encodeURIComponent(q)}`);
    sourceRef.current = es;

    es.onmessage = (event) => {
      handleEvent(JSON.parse(event.data));
    };
    es.onerror = () => es.close();
  }

  function handleEvent(payload) {
    if (payload.type === "source_complete") {
      setStats((s) => ({ ...s, sources: s.sources + 1 }));
    }
    if (payload.type === "escalation") {
      setStats((s) => ({ ...s, conflicts: s.conflicts + 1 }));
    }
    if (payload.type === "business_resolved") {
      const biz = payload.business;
      setBusinesses((prev) => [...prev, biz]);
      setStats((s) => ({
        ...s,
        found: s.found + 1,
        verified: s.verified + (biz.claims.some((c) => c.verdict === "Verified") ? 1 : 0),
      }));
    }
    if (payload.type === "done") {
      const result = payload.result;
      setSummaryText(result.research_summary_text || "");
      setStats((s) => ({ ...s, time: result.summary.research_duration_seconds }));
    }
  }

  return stage === "search" ? (
    <SearchScreen onSearch={runSearch} />
  ) : (
    <ResultsScreen
      query={query}
      businesses={businesses}
      stats={stats}
      summaryText={summaryText}
      onNewSearch={() => setStage("search")}
    />
  );
}
