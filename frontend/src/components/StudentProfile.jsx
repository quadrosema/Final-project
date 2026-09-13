export default function StudentProfile({ student }) {
  return <section className="panel"><h2>Student profile</h2><dl className="profile"><dt>Name</dt><dd>{student.name}</dd><dt>Major</dt><dd>{student.major}</dd><dt>Academic year</dt><dd>{student.academic_year}</dd><dt>Skills visualization</dt><dd><div className="skills">{student.skills?.length ? student.skills.map((skill) => <span key={skill}>{skill}</span>) : "No skills recorded"}</div></dd></dl></section>;
}
