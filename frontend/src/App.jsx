import { useEffect, useState } from "react";
import AdvisorPanel from "./components/AdvisorPanel";
import History from "./components/History";
import PerformanceCards from "./components/PerformanceCards";
import Recommendations from "./components/Recommendations";
import RiskPanel from "./components/RiskPanel";
import StudentForm from "./components/StudentForm";
import StudentProfile from "./components/StudentProfile";
import StudentSelector from "./components/StudentSelector";
import { api } from "./services/api";
import "./fixes.css";

export default function App() {
  const [students, setStudents] = useState([]);
  const [skills, setSkills] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [dashboard, setDashboard] = useState(null);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    Promise.all([api.getStudents(), api.getSkills()]).then(([profiles, availableSkills]) => {
      if (cancelled) return;
      setStudents(profiles);
      setSkills(availableSkills);
      setSelectedId(profiles[0]?.student_id ?? null);
    }).catch((err) => { if (!cancelled) setError(err.message); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    let cancelled = false;
    setDashboard(null);
    if (selectedId === null) return;
    setLoading(true);
    api.getDashboard(selectedId).then((data) => {
      if (!cancelled) setDashboard(data);
    }).catch((err) => { if (!cancelled) setError(err.message); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [selectedId]);

  const selectStudent = (id) => {
    setError("");
    setDashboard(null);
    setSelectedId(id);
    if (id === null) setLoading(false);
  };
  const runAdvisor = async () => {
    setBusy(true);
    setError("");
    try {
      await api.runAdvisor(selectedId);
      setDashboard(await api.getDashboard(selectedId));
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  };
  const saveStudent = async (data) => {
    setBusy(true);
    setError("");
    try {
      const saved = selectedId === null ? await api.createStudent(data) : await api.updateStudent(selectedId, data);
      setStudents(await api.getStudents());
      if (saved.student_id !== selectedId) setSelectedId(saved.student_id);
      else setDashboard(await api.getDashboard(saved.student_id));
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  };
  const student = selectedId === null ? null
    : dashboard?.student ?? students.find((item) => item.student_id === selectedId);
  return (
    <main>
      <header className="topbar"><div><p className="eyebrow">AI-Powered Student Success</p><h1>Academic Advisor Dashboard</h1></div></header>
      {error && <p className="error" role="alert">{error}</p>}
      <div className="layout">
        <aside>
          <StudentSelector students={students} selectedId={selectedId} disabled={busy || (loading && !students.length)} onSelect={selectStudent} onNew={() => selectStudent(null)} />
          <StudentForm student={student} skills={skills} disabled={busy || loading} onSave={saveStudent} />
        </aside>
        <section className="dashboard" aria-busy={loading || busy}>
          {loading ? <section className="panel"><p role="status">Loading student data…</p></section> : student ? <>
            <StudentProfile student={student} />
            <PerformanceCards student={student} />
            <div className="two-column">
              <RiskPanel prediction={dashboard?.latest_prediction} />
              <AdvisorPanel guidance={dashboard?.academic_guidance} loading={busy} onRun={runAdvisor} />
            </div>
            <Recommendations recommendations={dashboard?.recommendations} />
            <History predictions={dashboard?.prediction_history} recommendations={dashboard?.recommendation_history} />
          </> : <section className="panel"><p className="muted">Create a new student profile using the form to start the dashboard.</p></section>}
        </section>
      </div>
    </main>
  );
}
