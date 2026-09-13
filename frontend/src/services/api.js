const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function request(path, options = {}) {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    const detail = Array.isArray(payload.detail)
      ? payload.detail.map((item) => `${item.loc?.slice(1).join(".") || "Input"}: ${item.msg}`).join("; ")
      : payload.detail;
    throw new Error(detail ?? "The request could not be completed.");
  }
  return response.json();
}

export const api = {
  getStudents: () => request("/api/students"),
  getSkills: () => request("/api/skills"),
  getDashboard: (studentId) => request(`/api/dashboard/student/${studentId}`),
  createStudent: (data) => request("/api/students", { method: "POST", body: JSON.stringify(data) }),
  updateStudent: (studentId, data) =>
    request(`/api/students/${studentId}`, { method: "PUT", body: JSON.stringify(data) }),
  runAdvisor: (studentId) =>
    request("/api/advisor/run", { method: "POST", body: JSON.stringify({ student_id: studentId }) }),
  getStats: () => request("/api/dashboard/stats"),
};
