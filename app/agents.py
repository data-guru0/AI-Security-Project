import httpx
from typing import TypedDict
from langgraph.graph import StateGraph, END
from langsmith import traceable
from app.config import Config


class ResearchState(TypedDict):
    topic: str
    session_id: str
    search_results: list[str]
    summaries: list[str]
    report: str
    verified: bool
    error: str


@traceable(run_type="llm", name="TensorZero Inference")
async def _tz_call(config: Config, function_name: str, user_message: str) -> str:
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            f"{config.tensorzero_url}/v1/inference",
            json={
                "function_name": function_name,
                "input": {"messages": [{"role": "user", "content": user_message}]},
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["content"][0]["text"]


def build_graph(config: Config):
    async def search_node(state: ResearchState) -> dict:
        result = await _tz_call(
            config,
            "research_summarize",
            f"You are a research assistant. Find and list 5 key facts, recent developments, and important details about: {state['topic']}. Be thorough and specific.",
        )
        return {"search_results": [result]}

    async def summarize_node(state: ResearchState) -> dict:
        combined = "\n\n".join(state["search_results"])
        summary = await _tz_call(
            config,
            "research_summarize",
            f"Summarize these research findings into clear, structured bullet points:\n\n{combined}",
        )
        return {"summaries": [summary]}

    async def report_node(state: ResearchState) -> dict:
        combined = "\n\n".join(state["summaries"])
        report = await _tz_call(
            config,
            "report_write",
            f"Write a comprehensive, well-structured research report on the topic: '{state['topic']}'\n\nUse these summarized findings:\n{combined}\n\nInclude: Executive Summary, Key Findings, Analysis, and Conclusion.",
        )
        return {"report": report}

    async def verify_node(state: ResearchState) -> dict:
        check = await _tz_call(
            config,
            "research_summarize",
            f"Review this report for factual consistency and logical coherence. Reply with YES if it passes or NO with a brief reason if it fails:\n\n{state['report'][:3000]}",
        )
        return {"verified": check.strip().upper().startswith("YES")}

    workflow = StateGraph(ResearchState)
    workflow.add_node("search", search_node)
    workflow.add_node("summarize", summarize_node)
    workflow.add_node("report", report_node)
    workflow.add_node("verify", verify_node)
    workflow.set_entry_point("search")
    workflow.add_edge("search", "summarize")
    workflow.add_edge("summarize", "report")
    workflow.add_edge("report", "verify")
    workflow.add_edge("verify", END)
    return workflow.compile()
