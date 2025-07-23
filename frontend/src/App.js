import React, { useState } from "react";

function App() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [professor, setProfessor] = useState(null);

  const handleSearch = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setError("");
    setProfessor(null);
    try {
      const res = await fetch(`http://localhost:8080/professors/${encodeURIComponent(query)}`);
      if (!res.ok) throw new Error("Professor not found");
      const data = await res.json();
      setProfessor(data);
    } catch (err) {
      setError(err.message || "Error fetching professor");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-100 to-blue-100 flex flex-col items-center justify-start py-10 px-4">
      <header className="w-full max-w-2xl mx-auto text-center mb-10">
        <h1 className="text-4xl md:text-5xl font-extrabold text-purple-800 mb-2 drop-shadow-lg">
          🤖 UMD Professor Analyzer
        </h1>
        <p className="text-lg md:text-xl text-gray-700 mb-6">
          Search, analyze, and discover the best professors at UMD with real data, reviews, and AI-powered insights.
        </p>
        <div className="flex justify-center">
          <input
            type="text"
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSearch()}
            placeholder="Search professors (e.g., John Smith)"
            className="w-full max-w-md px-4 py-2 rounded-l-lg border-t border-b border-l border-gray-300 focus:outline-none focus:ring-2 focus:ring-purple-400"
          />
          <button
            className="px-5 py-2 bg-purple-600 text-white font-semibold rounded-r-lg hover:bg-purple-700 transition"
            onClick={handleSearch}
            disabled={loading}
          >
            {loading ? "Searching..." : "Search"}
          </button>
        </div>
        {error && <div className="text-red-600 mt-2">{error}</div>}
      </header>
      <main className="w-full max-w-2xl mx-auto">
        {professor && (
          <div className="bg-white rounded-xl shadow-lg p-6 flex flex-col md:flex-row items-center gap-6">
            <div className="flex-shrink-0 w-20 h-20 bg-purple-200 rounded-full flex items-center justify-center text-3xl font-bold text-purple-700">
              {professor.name.split(' ').map(n => n[0]).join('').toUpperCase()}
            </div>
            <div className="flex-1">
              <h3 className="text-xl font-semibold text-purple-800">{professor.name}</h3>
              <p className="text-gray-600 mb-2">Department: {professor.department}</p>
              <div className="flex flex-wrap gap-2 mb-2">
                {professor.tags && professor.tags.map(tag => (
                  <span key={tag} className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs font-medium">{tag}</span>
                ))}
              </div>
              <p className="text-gray-700 italic mb-2">
                {professor.nlp_summary}
              </p>
              <div className="flex items-center gap-4 mb-2">
                <span className="text-sm text-gray-500">Avg GPA: <span className="font-bold text-gray-800">{professor.planetterp?.avg_gpa ?? "-"}</span></span>
                <span className="text-sm text-gray-500">Courses: <span className="font-bold text-gray-800">{professor.planetterp?.num_courses ?? "-"}</span></span>
                <span className="text-sm text-gray-500">Sentiment: <span className="font-bold text-green-600">{professor.sentiment_trend?.[0]?.sentiment ?? "-"}</span></span>
              </div>
              <details className="mt-2">
                <summary className="cursor-pointer text-purple-600 hover:underline">Show Raw Reviews</summary>
                <ul className="list-disc pl-5 mt-2">
                  {professor.raw_reviews && professor.raw_reviews.map((r, i) => (
                    <li key={i} className="text-gray-600 text-sm mb-1">{r}</li>
                  ))}
                </ul>
              </details>
            </div>
          </div>
        )}
      </main>
      <footer className="mt-16 text-gray-400 text-xs">&copy; {new Date().getFullYear()} UMD Professor Analyzer</footer>
    </div>
  );
}

export default App;
