from __future__ import annotations
from typing import Literal, TypedDict
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field

class Plan(BaseModel):
    steps: list[str] = Field(min_length=2, max_length=6)
    success_criteria: list[str]

class Review(BaseModel):
    decision: Literal["ready", "revise"]
    feedback: str
    risk_level: Literal["low", "medium", "high"]

class AgentState(TypedDict):
    objective: str
    plan: list[str]
    findings: list[str]
    analysis: str
    review: dict
    revision: int
    status: str
    events: list[dict]
    result: str

def event(state: AgentState, agent: str, message: str) -> list[dict]:
    return state.get("events", []) + [{"agent": agent, "message": message}]

class OperationsWorkflow:
    def __init__(self, model: str) -> None:
        self.llm = ChatOpenAI(model=model, temperature=0)
        graph = StateGraph(AgentState)
        graph.add_node("planner", self.plan)
        graph.add_node("researcher", self.research)
        graph.add_node("analyst", self.analyze)
        graph.add_node("reviewer", self.review)
        graph.set_entry_point("planner")
        graph.add_edge("planner", "researcher")
        graph.add_edge("researcher", "analyst")
        graph.add_edge("analyst", "reviewer")
        graph.add_conditional_edges("reviewer", self.route_review, {"revise": "researcher", "ready": END})
        self.graph = graph.compile()

    def plan(self, state: AgentState) -> dict:
        prompt = "Create a short executable plan for this objective: " + state["objective"]
        output = self.llm.with_structured_output(Plan).invoke(prompt)
        return {"plan": output.steps, "status": "planning", "events": event(state, "planner", "Created a measurable plan.")}

    def research(self, state: AgentState) -> dict:
        prompt = f"""Objective: {state['objective']}
Plan: {state['plan']}
Reviewer feedback: {state.get('review', {}).get('feedback', 'none')}
Generate concise evidence, assumptions, and open questions. Do not claim live web access."""
        response = self.llm.invoke(prompt)
        return {"findings": [str(response.content)], "status": "researching", "events": event(state, "researcher", "Collected evidence and assumptions.")}

    def analyze(self, state: AgentState) -> dict:
        prompt = f"""Objective: {state['objective']}
Plan: {state['plan']}
Findings: {state['findings']}
Produce a decision brief with options, trade-offs, risks, and recommendation."""
        response = self.llm.invoke(prompt)
        return {"analysis": str(response.content), "status": "analyzing", "events": event(state, "analyst", "Produced the decision brief.")}

    def review(self, state: AgentState) -> dict:
        prompt = f"""Review this work for completeness and safety.
Objective: {state['objective']}
Analysis: {state['analysis']}
Revision number: {state.get('revision', 0)}
Return ready unless a material gap remains."""
        output = self.llm.with_structured_output(Review).invoke(prompt)
        revision = state.get("revision", 0)
        decision = output.decision if revision < 1 else "ready"
        return {"review": output.model_dump() | {"decision": decision}, "revision": revision + (decision == "revise"), "status": "awaiting_approval" if decision == "ready" else "revising", "events": event(state, "reviewer", output.feedback)}

    @staticmethod
    def route_review(state: AgentState) -> str:
        return state["review"]["decision"]

    def start(self, objective: str) -> AgentState:
        initial: AgentState = {"objective": objective, "plan": [], "findings": [], "analysis": "", "review": {}, "revision": 0, "status": "queued", "events": [], "result": ""}
        return self.graph.invoke(initial)

    def execute(self, state: AgentState) -> AgentState:
        result = f"""APPROVED EXECUTION BRIEF

Objective
{state['objective']}

Recommended plan
""" + "\n".join(f"{i+1}. {step}" for i, step in enumerate(state["plan"])) + f"""

Decision brief
{state['analysis']}

Review
{state['review'].get('feedback', '')}
"""
        return {**state, "result": result, "status": "completed", "events": event(state, "executor", "Human approval received; finalized execution brief.")}
