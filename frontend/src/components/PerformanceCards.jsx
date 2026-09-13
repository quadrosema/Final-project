export default function PerformanceCards({ student }) {
  const cards = [
    ["GPA", student.gpa.toFixed(2)],
    ["Attendance", `${student.attendance_rate}%`],
    ["Assignment completion", `${student.assignment_completion_rate}%`],
    ["Failed credits", student.failed_credits],
  ];
  return <section className="card-grid">{cards.map(([label, value]) => <article className="metric-card" key={label}><span>{label}</span><strong>{value}</strong></article>)}</section>;
}
