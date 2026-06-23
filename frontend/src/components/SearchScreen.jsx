import { useState } from "react";

const EXAMPLES = ["Dentists in Austin", "Plumbers in Houston", "Family Lawyers in Chicago"];

export default function SearchScreen({ onSearch }) {
  const [value, setValue] = useState("");

  return (
    <div className="screen search-screen">
      <h1>EvidenceIQ</h1>
      <p className="tagline">Every fact must earn trust.</p>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (value.trim()) onSearch(value.trim());
        }}
      >
        <input
          className="search-input"
          placeholder='e.g. "Cardiologists in Birmingham"'
          value={value}
          onChange={(e) => setValue(e.target.value)}
        />
        <div className="chip-row">
          {EXAMPLES.map((ex) => (
            <button type="button" key={ex} className="chip" onClick={() => setValue(ex)}>
              {ex}
            </button>
          ))}
        </div>
        <button type="submit" className="search-button">
          SEARCH
        </button>
      </form>
    </div>
  );
}
