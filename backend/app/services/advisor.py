from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class AdvisorState(TypedDict, total=False):
    student: dict
    risk: dict
    recommendations: list[dict]
    risk_analysis: str
    course_analysis: str
    academic_guidance: str


def risk_analyzer(state: AdvisorState) -> AdvisorState:
    risk = state["risk"]
    return {
        "risk_analysis": (
            f"The student is classified as {risk['risk_level']} with a confidence score of "
            f"{risk['risk_score']}%. Key indicators: {', '.join(risk['academic_indicators'])}."
        )
    }


def skill_course_analyzer(state: AdvisorState) -> AdvisorState:
    titles = ", ".join(item["course_title"] for item in state["recommendations"])
    skills = ", ".join(state["student"]["skills"]) or "no recorded skills"
    return {
        "course_analysis": (
            f"Recorded skills are {skills}. The strongest learning opportunities are {titles}."
        )
    }


def academic_advisor(state: AdvisorState) -> AdvisorState:
    risk = state["risk"]
    action = (
        "Prioritize a meeting with an academic advisor, create a weekly recovery plan, and use tutoring support."
        if risk["risk_level"] == "High Risk"
        else "Continue monitoring performance and schedule regular study time for the recommended courses."
    )
    return {
        "academic_guidance": (
            f"{state['risk_analysis']} {state['course_analysis']} {action} "
            "Choose courses only after confirming prerequisites and workload with your academic advisor."
        )
    }


def build_advisor_graph():
    graph = StateGraph(AdvisorState)
    graph.add_node("risk_analyzer", risk_analyzer)
    graph.add_node("skill_course_analyzer", skill_course_analyzer)
    graph.add_node("academic_advisor", academic_advisor)
    graph.add_edge(START, "risk_analyzer")
    graph.add_edge("risk_analyzer", "skill_course_analyzer")
    graph.add_edge("skill_course_analyzer", "academic_advisor")
    graph.add_edge("academic_advisor", END)
    return graph.compile()
