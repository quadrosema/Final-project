export default function RiskPanel({ prediction }) {
  if (!prediction) return <section className="panel"><h2>Academic risk</h2><p className="muted">Run the advisor workflow to receive an academic risk prediction.</p></section>;
  const riskClass = prediction.risk_level.toLowerCase().replace(" ", "-");
  return <section className="panel"><h2>Academic risk</h2><div className={`risk ${riskClass}`}>{prediction.risk_level}</div><p><strong>Risk score:</strong> {prediction.risk_score}%</p><p className="muted">Confidence in the predicted class, not a probability of academic failure.</p><p><strong>Relevant academic indicators</strong></p>{prediction.indicators_source === "current_profile" && <p className="muted">Older prediction: these indicators describe the current profile, not the original prediction.</p>}<ul>{prediction.academic_indicators?.map((indicator) => <li key={indicator}>{indicator}</li>)}</ul></section>;
}
