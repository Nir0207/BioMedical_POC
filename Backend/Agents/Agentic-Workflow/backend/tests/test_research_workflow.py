import pytest

from agentic_api.workflows.research_workflow import AgenticResearchWorkflow


class FakeTools:
    def __init__(self, scenario: str) -> None:
        self.scenario = scenario
        self.compound_tool_calls = 0

    async def search_disease(self, query: str, limit: int = 10):
        query_norm = query.strip().lower()
        if self.scenario == "compound_intent":
            if query_norm in {"parkinson disease", "which compounds are linked to parkinson disease targets"}:
                return [
                    {
                        "id": "MONDO_0005180",
                        "name": "Parkinson disease",
                        "phrase_score": 4,
                        "token_hits": 2,
                        "synonym_hit": 1,
                    }
                ]
            return []
        if self.scenario == "ambiguous_short_query":
            if query_norm == "foo":
                return [
                    {"id": "MONDO_1111111", "name": "Foo disease", "phrase_score": 2, "token_hits": 1, "synonym_hit": 0},
                    {"id": "MONDO_2222222", "name": "Foo syndrome", "phrase_score": 2, "token_hits": 1, "synonym_hit": 0},
                ]
            return []
        if self.scenario == "nl_query_requires_extraction":
            if query_norm == "breast cancer":
                return [{"id": "MONDO_0007254", "name": "breast cancer", "phrase_score": 4, "token_hits": 2, "synonym_hit": 0}]
            return []
        if self.scenario == "no_entity":
            return []
        return [{"id": "MONDO_0007254", "name": "breast cancer", "phrase_score": 4, "token_hits": 2, "synonym_hit": 0}]

    async def search_gene(self, query: str, limit: int = 10):
        return [{"id": "ENSG00000141510", "symbol": "TP53"}]

    async def search_protein(self, query: str, limit: int = 10):
        return [{"id": "UNIPROT:P04637", "name": "Cellular tumor antigen p53"}]

    async def get_disease_target_graph(self, disease_id: str, limit: int = 100):
        if self.scenario == "compound_intent":
            return {
                "disease": {"id": disease_id, "name": "Parkinson disease"},
                "associated_genes": [
                    {"id": "ENSG00000128272", "symbol": "SNCA", "name": "SNCA"},
                    {"id": "ENSG00000150136", "symbol": "LRRK2", "name": "LRRK2"},
                ],
                "proteins": [],
                "interaction_partners": [],
                "pathways": [],
                "compounds": [],
                "compound_signals": [
                    {
                        "id": "CHEMBL_SIGNAL:ENSG00000128272",
                        "name": "Known-drug evidence (ChEMBL) for target SNCA",
                        "target_gene_symbol": "SNCA",
                        "source": "OpenTargets",
                        "inferred": True,
                    }
                ],
                "evidence_summary": {"evidence_count": 2, "source_breakdown": {"Open Targets": 2}},
            }
        return {
            "disease": {"id": disease_id, "name": "breast cancer"},
            "associated_genes": [
                {"id": "ENSG00000141510", "symbol": "TP53", "name": "TP53"},
                {"id": "ENSG00000146648", "symbol": "EGFR", "name": "EGFR"},
            ],
            "proteins": [{"id": "UNIPROT:P04637", "name": "p53"}],
            "interaction_partners": [{"id": "UNIPROT:Q00987", "name": "MDM2"}],
            "pathways": [{"id": "R-HSA-69563", "name": "p53 pathway"}],
            "compounds": [{"id": "CHEMBL123", "name": "Example compound"}],
            "compound_signals": [],
            "evidence_summary": {"evidence_count": 2, "source_breakdown": {"Open Targets": 2}},
        }

    async def get_protein_neighbors(self, protein_id: str, depth: int = 2):
        return {"center_id": protein_id, "depth": depth, "nodes": [], "edges": []}

    async def get_pathway_context(self, protein_ids, limit: int = 100):
        return [{"id": "R-HSA-69563", "name": "p53 pathway"}]

    async def get_compounds_for_targets(self, protein_ids, target_gene_ids=None, disease_id=None, limit: int = 100):
        self.compound_tool_calls += 1
        if self.scenario == "compound_intent":
            return [{"id": "CHEMBL1201575", "name": "Safinamide", "source": "ChEMBL", "inferred": False}]
        return [{"id": "CHEMBL123", "name": "Example compound"}]

    async def retrieve_evidence_chunks(self, query: str, top_k: int = 8, disease_id=None):
        if self.scenario == "insufficient_evidence":
            return []
        if self.scenario == "compound_intent":
            return [
                {
                    "id": "EV-002",
                    "text": "Known-drug evidence from ChEMBL exists for Parkinson disease targets",
                    "source": "Open Targets",
                }
            ]
        return [
            {
                "id": "EV-001",
                "text": "TP53 has high-confidence association in Open Targets",
                "source": "Open Targets",
            }
        ]

    async def rank_targets(self, graph_results, evidence_results):
        return [{"gene_id": "ENSG00000141510", "gene_symbol": "TP53", "score": 5.0}]

    async def build_graph_payload(self, entity_id: str, depth: int = 2):
        return {
            "center_id": entity_id,
            "depth": depth,
            "nodes": [{"id": entity_id, "label": "breast cancer", "type": "Disease", "properties": {}}],
            "edges": [],
        }


@pytest.mark.asyncio
async def test_workflow_happy_path_returns_answer_and_citations():
    workflow = AgenticResearchWorkflow(
        tools=FakeTools("happy"),
        reasoning_model="qwen2.5:7b",
        base_url="http://localhost:11434",
        llm_enabled=False,
    )

    state = await workflow.run("Find disease targets for breast cancer", top_k=6)

    assert state["intent"] == "target_discovery"
    assert state["resolved_entities"]
    assert state["ranking_results"]
    assert "Disease:" in state["final_answer"]
    assert state["citations"]


@pytest.mark.asyncio
async def test_workflow_no_entity_path_returns_error_message():
    workflow = AgenticResearchWorkflow(
        tools=FakeTools("no_entity"),
        reasoning_model="qwen2.5:7b",
        base_url="http://localhost:11434",
        llm_enabled=False,
    )

    state = await workflow.run("asdfghjkl", top_k=6)

    assert not state["resolved_entities"]
    assert state["errors"]
    assert "No disease entities found" in state["errors"][0]
    assert "Workflow ended with errors" in state["final_answer"]


@pytest.mark.asyncio
async def test_workflow_insufficient_evidence_path_is_bounded():
    workflow = AgenticResearchWorkflow(
        tools=FakeTools("insufficient_evidence"),
        reasoning_model="qwen2.5:7b",
        base_url="http://localhost:11434",
        llm_enabled=False,
    )

    state = await workflow.run("targets for breast cancer", top_k=6)

    assert state["resolved_entities"]
    assert not state["evidence_results"]
    assert "Insufficient evidence" in state["errors"][0]
    assert "graph-only guidance" in state["final_answer"].lower()


@pytest.mark.asyncio
async def test_workflow_extracts_disease_from_natural_language_query():
    workflow = AgenticResearchWorkflow(
        tools=FakeTools("nl_query_requires_extraction"),
        reasoning_model="qwen2.5:7b",
        base_url="http://localhost:11434",
        llm_enabled=False,
    )

    state = await workflow.run("Find key targets for breast cancer and summarize evidence", top_k=6)

    assert state["resolved_entities"]
    assert state["resolved_entities"][0]["id"] == "MONDO_0007254"
    assert "Workflow ended with errors" not in state["final_answer"]


@pytest.mark.asyncio
async def test_workflow_compound_intent_uses_compound_fallback():
    tools = FakeTools("compound_intent")
    workflow = AgenticResearchWorkflow(
        tools=tools,
        reasoning_model="qwen2.5:7b",
        base_url="http://localhost:11434",
        llm_enabled=False,
    )

    state = await workflow.run("Which compounds are linked to Parkinson disease targets?", top_k=6)

    assert state["intent"] == "compound_target_discovery"
    assert state["requires_compounds"] is True
    assert state["resolved_entities"][0]["id"] == "MONDO_0005180"
    assert state["graph_results"]["compounds"]
    assert tools.compound_tool_calls >= 1
    assert "Workflow ended with errors" not in state["final_answer"]


@pytest.mark.asyncio
async def test_workflow_ambiguous_single_term_prompts_clarification():
    workflow = AgenticResearchWorkflow(
        tools=FakeTools("ambiguous_short_query"),
        reasoning_model="qwen2.5:7b",
        base_url="http://localhost:11434",
        llm_enabled=False,
    )

    state = await workflow.run("foo", top_k=6)

    assert not state["resolved_entities"]
    assert state["errors"]
    assert "ambiguous" in state["errors"][0].lower()
    assert "Workflow ended with errors" in state["final_answer"]
