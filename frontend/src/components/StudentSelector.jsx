import { useMemo, useState } from "react";

export default function StudentSelector({ students, selectedId, onSelect, onNew, disabled }) {
  const [query, setQuery] = useState("");
  const filteredStudents = useMemo(
    () => students.filter((student) => `${student.name} ${student.major}`.toLowerCase().includes(query.toLowerCase())),
    [students, query],
  );

  return (
    <section className="panel student-selector">
      <button type="button" onClick={onNew} disabled={disabled}>New student</button>
      <label htmlFor="student-search">Search or filter students</label>
      <input id="student-search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Name or major" />
      <div className="student-list">
        {filteredStudents.length ? filteredStudents.map((student) => (
          <button disabled={disabled} key={student.student_id} className={selectedId === student.student_id ? "selected" : ""} onClick={() => onSelect(student.student_id)}>
            <strong>{student.name}</strong><span>{student.major}</span>
          </button>
        )) : <p className="muted">No students match this filter.</p>}
      </div>
    </section>
  );
}
