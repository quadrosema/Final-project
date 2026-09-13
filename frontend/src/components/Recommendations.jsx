import CourseCard from "./CourseCard";

export default function Recommendations({ recommendations }) {
  return <section className="panel"><h2>Recommended courses</h2>{recommendations?.length ? <div className="recommendations">{recommendations.map((course) => <CourseCard course={course} key={course.course_id} />)}</div> : <p className="muted">No course recommendations yet.</p>}</section>;
}
