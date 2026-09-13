export default function AdvisorPanel({ guidance, loading, onRun }) {
  return <section className="panel advisor"><div><h2>AI academic advice</h2><p>{guidance || "Run the LangGraph academic advisor for personalized guidance."}</p></div><button onClick={onRun} disabled={loading}>{loading ? "Analyzing…" : "Run academic advisor"}</button></section>;
}
