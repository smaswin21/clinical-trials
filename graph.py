from langgraph.graph import StateGraph, END

from agents.extractor import extractor_node
from agents.searcher import searcher_node
from agents.matcher import matcher_node
from agents.explainer import explainer_node
from config.state import ClinicalTrialState


def _route_after_searcher(state: ClinicalTrialState) -> str:
	return "matcher" if state.get("candidate_trials") else "explainer"


workflow = StateGraph(ClinicalTrialState)

workflow.add_node("extractor", extractor_node)
workflow.add_node("searcher", searcher_node)
workflow.add_node("matcher", matcher_node)
workflow.add_node("explainer", explainer_node)

workflow.set_entry_point("extractor")
workflow.add_edge("extractor", "searcher")
workflow.add_conditional_edges(
	"searcher",
	_route_after_searcher,
	{"matcher": "matcher", "explainer": "explainer"},
)
workflow.add_edge("matcher", "explainer")
workflow.add_edge("explainer", END)

graph = workflow.compile()
