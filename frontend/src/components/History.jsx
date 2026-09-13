import CourseCard from "./CourseCard";

export default function History({ predictions, recommendations }) {
  return <section className="panel"><h2>History</h2><div className="history-grid">
    <div><h3>Risk predictions</h3>{predictions?.length ? predictions.map((item) => <details key={item.id} className="history-event">
      <summary>{item.risk_level} ({item.risk_score}% confidence) — {new Date(item.created_at).toLocaleString()}</summary>
      {item.indicators_source === "current_profile" && <p className="muted">Older prediction: original indicators were not recorded. These indicators describe the current profile.</p>}
      <ul>{item.academic_indicators?.map((indicator) => <li key={indicator}>{indicator}</li>)}</ul>
      {item.feature_snapshot && <p className="muted">Recorded GPA: {item.feature_snapshot.gpa}; attendance: {item.feature_snapshot.attendance_rate}%; completion: {item.feature_snapshot.assignment_completion_rate}%; failed credits: {item.feature_snapshot.failed_credits}.</p>}
    </details>) : <p className="muted">No risk predictions recorded.</p>}</div>
    <div><h3>Course recommendations</h3>{recommendations?.length ? recommendations.map((item) => <details key={item.id} className="history-event">
      <summary>{item.recommendations?.map((course) => course.course_title).join(", ")} — {new Date(item.created_at).toLocaleString()}</summary>
      {item.recommendations?.map((course) => <CourseCard key={course.course_id} course={course} />)}
      {item.academic_guidance && <p>{item.academic_guidance}</p>}
    </details>) : <p className="muted">No recommendation events recorded.</p>}</div>
  </div></section>;
}
