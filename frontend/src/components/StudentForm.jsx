import { useEffect, useState } from "react";

const blankStudent = { name: "", major: "", academic_year: "", gpa: "0", attendance_rate: "0", assignment_completion_rate: "0", failed_credits: "0", interests: "", skill_ids: [] };
const fields = [
  { name: "name", label: "Name" },
  { name: "major", label: "Major" },
  { name: "academic_year", label: "Academic year" },
  { name: "gpa", label: "GPA", type: "number", min: 0, max: 4, step: "any" },
  { name: "attendance_rate", label: "Attendance rate", type: "number", min: 0, max: 100, step: "any" },
  { name: "assignment_completion_rate", label: "Assignment completion rate", type: "number", min: 0, max: 100, step: "any" },
  { name: "failed_credits", label: "Failed credits", type: "number", min: 0, step: 1 },
  { name: "interests", label: "Interests", optional: true },
];

export default function StudentForm({ student, skills, onSave, disabled }) {
  const [form, setForm] = useState(blankStudent);
  useEffect(() => {
    setForm(student ? {
      ...Object.fromEntries(fields.map(({ name }) => [name, String(student[name] ?? "")])),
      skill_ids: student.skill_ids ?? [],
    } : blankStudent);
  }, [student]);
  const setValue = (event) => setForm((current) => ({ ...current, [event.target.name]: event.target.value }));
  const toggleSkill = (skillId) => setForm((current) => ({ ...current, skill_ids: current.skill_ids.includes(skillId) ? current.skill_ids.filter((id) => id !== skillId) : [...current.skill_ids, skillId] }));
  const submit = (event) => {
    event.preventDefault();
    const payload = { ...form };
    fields.forEach(({ name, type }) => { if (type === "number") payload[name] = Number(form[name]); });
    onSave(payload);
  };
  return (
    <section className="panel">
      <h2>{student ? "Update student profile" : "New student profile"}</h2>
      <form onSubmit={submit}>
        <fieldset disabled={disabled} className="student-form form-fields">
          {fields.map(({ name, label, type = "text", optional, ...bounds }) => <label key={name}>{label}<input name={name} type={type} value={form[name]} onChange={setValue} required={!optional} {...bounds} /></label>)}
          <fieldset><legend>Skills</legend>{skills.map((skill) => <label className="checkbox" key={skill.skill_id}><input type="checkbox" checked={form.skill_ids.includes(skill.skill_id)} onChange={() => toggleSkill(skill.skill_id)} />{skill.skill_name} ({skill.category})</label>)}</fieldset>
          <button type="submit">{disabled ? "Please wait…" : "Save profile"}</button>
        </fieldset>
      </form>
    </section>
  );
}
