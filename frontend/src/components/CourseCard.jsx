export default function CourseCard({ course }) {
  const recordedScore = course.similarity_score !== null && course.similarity_score !== undefined;
  return <article className="recommendation">
    <header><h3>{course.course_title}</h3><strong>{recordedScore ? `${course.match_percentage}% match` : "Score not recorded"}</strong></header>
    {recordedScore && <p><strong>Similarity score:</strong> {course.similarity_score}</p>}
    {recordedScore && <p><strong>Relevant skills:</strong> {course.relevant_skills?.join(", ") || "Profile and interests"}</p>}
    <p>{course.explanation}</p>
  </article>;
}
