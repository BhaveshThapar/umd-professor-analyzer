import React, { useState } from "react";

function App() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [professor, setProfessor] = useState(null);
  const [notFound, setNotFound] = useState(false);
  const [sourcesFound, setSourcesFound] = useState(null);
  const [noData, setNoData] = useState(false);
  const [qaQuestion, setQaQuestion] = useState("");
  const [qaAnswer, setQaAnswer] = useState("");
  const [qaLoading, setQaLoading] = useState(false);

  const handleSearch = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setError("");
    setProfessor(null);
    setNotFound(false);
    setSourcesFound(null);
    setNoData(false);
    try {
      const res = await fetch(`http://localhost:8080/professors/${encodeURIComponent(query)}`);
      if (!res.ok) throw new Error("Professor not found");
      const data = await res.json();
      setSourcesFound(data.sources_found || null);
      setNoData(data.no_data || false);
      if (data.no_data) {
        setNotFound(true);
        setProfessor(null);
      } else {
        setProfessor(data);
        setNotFound(false);
      }
    } catch (err) {
      setError(err.message || "Error fetching professor");
      setNotFound(true);
      setProfessor(null);
      setSourcesFound(null);
      setNoData(false);
    } finally {
      setLoading(false);
    }
  };

  const handleQa = async () => {
    if (!qaQuestion.trim() || !professor) return;
    setQaLoading(true);
    setQaAnswer("");
    try {
      const res = await fetch(`http://localhost:8000/qa`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reviews: professor.raw_reviews, question: qaQuestion })
      });
      if (!res.ok) throw new Error("Q&A failed");
      const data = await res.json();
      setQaAnswer(data.answer || "No answer found.");
    } catch (err) {
      setQaAnswer("Error: " + (err.message || "Q&A failed"));
    } finally {
      setQaLoading(false);
    }
  };

  const renderSourcesStatus = () => {
    if (!sourcesFound) return null;
    const available = Object.entries(sourcesFound).filter(([k, v]) => v).map(([k]) => k);
    const missing = Object.entries(sourcesFound).filter(([k, v]) => !v).map(([k]) => k);
    if (available.length === 0) {
      return <div className="text-red-500 text-sm mb-2">No reviews found from Reddit, Coursicle, or RMP.</div>;
    }
    if (missing.length > 0) {
      return (
        <div className="text-yellow-600 text-sm mb-2">
          No reviews found from: {missing.join(", ")}. Showing data from: {available.join(", ")}.
        </div>
      );
    }
    return (
      <div className="text-green-600 text-sm mb-2">Reviews found from all sources: Reddit, Coursicle, RMP.</div>
    );
  };

  const isRealTags = tags => Array.isArray(tags) && tags.length > 0 && !tags.some(tag => tag.toLowerCase().includes("stub") || tag === "No curves" || tag === "Project heavy" || tag === "Explains concepts well");
  const isRealSummary = summary => summary && !summary.toLowerCase().includes("stub") && summary !== "Challenging but fair. Weekly quizzes and lots of projects.";

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-100 to-blue-100 flex flex-col items-center justify-start py-10 px-4">
      <header className="w-full max-w-2xl mx-auto text-center mb-10">
        <h1 className="text-4xl md:text-5xl font-extrabold text-purple-800 mb-2 drop-shadow-lg">
          UMD Professor Analyzer
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
        {notFound && (
          <div className="bg-white rounded-xl shadow-lg p-8 text-center text-xl text-gray-600 font-semibold">
            No Professor Found
          </div>
        )}
        {professor && (
          <div className="bg-white rounded-xl shadow-lg p-6 flex flex-col md:flex-row items-center gap-6">
            <div className="flex-shrink-0 w-20 h-20 bg-purple-200 rounded-full flex items-center justify-center text-3xl font-bold text-purple-700">
              {professor.name.split(' ').map(n => n[0]).join('').toUpperCase()}
            </div>
            <div className="flex-1">
              <h3 className="text-xl font-semibold text-purple-800">{professor.name}</h3>
              <p className="text-gray-600 mb-2">Department: {professor.department}</p>
              {renderSourcesStatus()}
              {isRealTags(professor.tags) ? (
                <div className="flex flex-wrap gap-2 mb-2">
                  {professor.tags.map(tag => (
                    <span key={tag} className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs font-medium">{tag}</span>
                  ))}
                </div>
              ) : (
                <div className="text-gray-400 text-sm mb-2">Not enough data to extract tags.</div>
              )}
              {Array.isArray(professor.skills) && professor.skills.length > 0 ? (
                <div className="flex flex-wrap gap-2 mb-2">
                  <span className="text-xs font-semibold text-purple-700 mr-2">Skills/Topics:</span>
                  {professor.skills.map(skill => (
                    <span key={skill} className="bg-green-100 text-green-800 px-2 py-1 rounded text-xs font-medium">{skill}</span>
                  ))}
                </div>
              ) : null}
              <p className="text-gray-700 italic mb-2">
                {isRealSummary(professor.nlp_summary) ? professor.nlp_summary : "Not enough data to summarize."}
              </p>
              {professor.sentiment_explanation && (
                <div className="text-blue-700 text-xs mb-2">Sentiment: {professor.sentiment_explanation}</div>
              )}
              {professor.toxic_reviews === true && (
                <div className="text-red-600 text-xs mb-2 font-bold">Warning: Some reviews may be toxic, sarcastic, or inappropriate.</div>
              )}
              <div className="flex items-center gap-4 mb-2">
                <span className="text-sm text-gray-500">Avg GPA: <span className="font-bold text-gray-800">{professor.planetterp?.avg_gpa ?? "-"}</span></span>
                <span className="text-sm text-gray-500">Courses: <span className="font-bold text-gray-800">{professor.planetterp?.num_courses ?? "-"}</span></span>
                <span className="text-sm text-gray-500">
                  Sentiment: {professor.sentiment_trend?.[0]?.sentiment != null
                    ? <span className="font-bold text-green-600">{professor.sentiment_trend[0].sentiment}</span>
                    : <span className="font-bold text-gray-400">-</span>
                  }
                </span>
              </div>
              <details className="mt-2">
                <summary className="cursor-pointer text-purple-600 hover:underline">Show Raw Reviews</summary>
                <ul className="list-disc pl-5 mt-2 max-w-full break-words overflow-x-auto">
                  {professor.raw_reviews && professor.raw_reviews.map((r, i) => (
                    <li key={i} className="text-gray-600 text-sm mb-1 whitespace-pre-line break-words max-w-full overflow-x-auto">
                      {r}
                    </li>
                  ))}
                </ul>
              </details>
              {}
              <div className="mt-4 mb-2">
                <div className="font-semibold text-sm text-gray-700 mb-1">Ask a question about this professor:</div>
                <div className="flex gap-2 mb-2">
                  <input
                    type="text"
                    value={qaQuestion}
                    onChange={e => setQaQuestion(e.target.value)}
                    placeholder="e.g. Does this professor curve grades?"
                    className="w-full px-3 py-1 rounded border border-gray-300 focus:outline-none focus:ring-2 focus:ring-purple-400"
                  />
                  <button
                    className="px-4 py-1 bg-purple-600 text-white font-semibold rounded hover:bg-purple-700 transition"
                    onClick={handleQa}
                    disabled={qaLoading || !qaQuestion.trim()}
                  >
                    {qaLoading ? "Asking..." : "Ask"}
                  </button>
                </div>
                {qaAnswer && (
                  <div className="bg-gray-100 rounded p-2 text-sm text-gray-800 mt-1">
                    <span className="font-semibold text-purple-700">LLM Answer:</span> {qaAnswer}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </main>
      <footer className="mt-16 text-gray-400 text-xs">&copy; {new Date().getFullYear()} UMD Professor Analyzer</footer>
    </div>
  );
}

export default App;
