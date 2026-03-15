from __future__ import annotations

import json
import re
from typing import Any, TypedDict

from langchain_ollama import ChatOllama
from langgraph.graph import END, StateGraph

from agentic_api.tools.fixed_tools import FixedResearchTools


class ResearchWorkflowState(TypedDict, total=False):
    user_query: str
    normalized_query: str
    intent: str
    module: str
    resolved_entities: list[dict[str, Any]]
    graph_query_plan: dict[str, Any]
    graph_results: dict[str, Any]
    evidence_results: list[dict[str, Any]]
    ranking_results: list[dict[str, Any]]
    final_answer: str
    citations: list[dict[str, Any]]
    graph_payload: dict[str, Any]
    errors: list[str]
    resolution_notes: list[str]
    top_k: int
    ranking_required: bool
    requires_compounds: bool


class AgenticResearchWorkflow:
    DISEASE_ALIASES: dict[str, str] = {
        "parkinson": "parkinson disease",
        "parkinsons": "parkinson disease",
        "parkinson's": "parkinson disease",
        "alzheimers": "alzheimer disease",
        "alzheimer's": "alzheimer disease",
        "breast tumor": "breast cancer",
        "breast carcinoma": "breast cancer",
        "lung tumor": "lung cancer",
        "t2d": "type 2 diabetes mellitus",
        "type 2 diabetes": "type 2 diabetes mellitus",
        "diabetes type 2": "type 2 diabetes mellitus",
        "ra": "rheumatoid arthritis",
        "ms": "multiple sclerosis",
    }

    QUERY_STOPWORDS = {
        "find",
        "show",
        "list",
        "give",
        "tell",
        "summarize",
        "summary",
        "evidence",
        "key",
        "top",
        "best",
        "important",
        "targets",
        "target",
        "for",
        "of",
        "in",
        "about",
        "on",
        "and",
        "with",
        "related",
        "associated",
        "discover",
        "discovery",
        "what",
        "which",
        "please",
        "linked",
        "link",
        "links",
        "are",
        "is",
        "to",
        "identify",
        "research",
        "query",
        "could",
        "you",
    }

    COMPOUND_HINT_TERMS = {
        "compound",
        "compounds",
        "drug",
        "drugs",
        "chembl",
        "small molecule",
        "small-molecule",
    }

    TARGET_HINT_TERMS = {
        "target",
        "targets",
        "gene",
        "genes",
        "protein",
        "proteins",
        "pathway",
        "pathways",
        "disease",
    }

    def __init__(
        self,
        tools: FixedResearchTools,
        reasoning_model: str,
        base_url: str,
        llm_enabled: bool,
    ) -> None:
        self.tools = tools
        self.llm_enabled = llm_enabled
        self.reasoner = ChatOllama(model=reasoning_model, base_url=base_url, temperature=0.1) if llm_enabled else None
        self.app = self._build_graph()

    async def run(self, user_query: str, top_k: int = 8) -> ResearchWorkflowState:
        state: ResearchWorkflowState = {
            "user_query": user_query,
            "normalized_query": "",
            "intent": "",
            "module": "",
            "resolved_entities": [],
            "graph_query_plan": {},
            "graph_results": {},
            "evidence_results": [],
            "ranking_results": [],
            "final_answer": "",
            "citations": [],
            "graph_payload": {},
            "errors": [],
            "resolution_notes": [],
            "top_k": top_k,
            "ranking_required": False,
            "requires_compounds": False,
        }
        return await self.app.ainvoke(state)

    def _build_graph(self):
        graph = StateGraph(ResearchWorkflowState)

        graph.add_node("query_intake", self.query_intake)
        graph.add_node("intent_module_router", self.intent_module_router)
        graph.add_node("entity_resolution", self.entity_resolution)
        graph.add_node("graph_query_planning", self.graph_query_planning)
        graph.add_node("graph_retrieval", self.graph_retrieval)
        graph.add_node("evidence_retrieval", self.evidence_retrieval)
        graph.add_node("optional_ranking", self.optional_ranking)
        graph.add_node("answer_synthesis", self.answer_synthesis)
        graph.add_node("response_formatting", self.response_formatting)

        graph.set_entry_point("query_intake")
        graph.add_edge("query_intake", "intent_module_router")
        graph.add_edge("intent_module_router", "entity_resolution")
        graph.add_conditional_edges(
            "entity_resolution",
            self.route_after_entity_resolution,
            {
                "graph_query_planning": "graph_query_planning",
                "response_formatting": "response_formatting",
            },
        )
        graph.add_edge("graph_query_planning", "graph_retrieval")
        graph.add_edge("graph_retrieval", "evidence_retrieval")
        graph.add_conditional_edges(
            "evidence_retrieval",
            self.route_after_evidence,
            {
                "optional_ranking": "optional_ranking",
                "answer_synthesis": "answer_synthesis",
            },
        )
        graph.add_edge("optional_ranking", "answer_synthesis")
        graph.add_edge("answer_synthesis", "response_formatting")
        graph.add_edge("response_formatting", END)

        return graph.compile()

    async def query_intake(self, state: ResearchWorkflowState) -> ResearchWorkflowState:
        normalized = " ".join(state.get("user_query", "").split())
        return {"normalized_query": normalized}

    async def intent_module_router(self, state: ResearchWorkflowState) -> ResearchWorkflowState:
        query = state.get("normalized_query", "").lower()
        requires_compounds = any(term in query for term in self.COMPOUND_HINT_TERMS)

        if requires_compounds:
            return {
                "intent": "compound_target_discovery",
                "module": "disease_target_discovery",
                "requires_compounds": True,
            }
        if any(word in query for word in self.TARGET_HINT_TERMS):
            return {
                "intent": "target_discovery",
                "module": "disease_target_discovery",
                "requires_compounds": False,
            }
        return {
            "intent": "graph_exploration",
            "module": "disease_target_discovery",
            "requires_compounds": False,
        }

    async def entity_resolution(self, state: ResearchWorkflowState) -> ResearchWorkflowState:
        query = state.get("normalized_query", "")
        candidates = self._build_disease_search_candidates(query)

        scored_hits: dict[str, dict[str, Any]] = {}
        for candidate_rank, candidate in enumerate(candidates):
            rows = await self.tools.search_disease(query=candidate, limit=7)
            if not rows:
                continue

            alias_boost = 2.0 if self._is_alias_candidate(candidate, query) else 0.0
            for row in rows:
                row_id = self._safe_string(row.get("id"))
                if not row_id:
                    continue
                score = self._score_disease_hit(
                    original_query=query,
                    candidate=candidate,
                    row=row,
                    candidate_rank=candidate_rank,
                    alias_boost=alias_boost,
                )
                previous = scored_hits.get(row_id)
                if not previous or score > previous["score"]:
                    scored_hits[row_id] = {
                        "id": row_id,
                        "name": row.get("name", row_id),
                        "score": score,
                        "candidate": candidate,
                    }

        if not scored_hits:
            return {
                "resolved_entities": [],
                "errors": state.get("errors", []) + [
                    "No disease entities found for query. Try naming a disease explicitly, for example: Parkinson disease or breast cancer."
                ],
            }

        ranked_hits = sorted(scored_hits.values(), key=lambda item: item["score"], reverse=True)
        best = ranked_hits[0]
        query_terms = self._query_terms(query)

        if best["score"] < 2.0:
            suggestions = ", ".join(f"{hit['name']} ({hit['id']})" for hit in ranked_hits[:3])
            return {
                "resolved_entities": [],
                "errors": state.get("errors", [])
                + [f"Disease resolution confidence is too low. Try one of: {suggestions}"],
            }

        resolution_notes = state.get("resolution_notes", [])
        if len(ranked_hits) > 1:
            gap = best["score"] - ranked_hits[1]["score"]
            short_query = len(query_terms) <= 1
            if short_query and gap < 1.0:
                suggestions = ", ".join(f"{hit['name']} ({hit['id']})" for hit in ranked_hits[:3])
                return {
                    "resolved_entities": [],
                    "errors": state.get("errors", [])
                    + [f"Query is ambiguous across multiple diseases. Please clarify with one of: {suggestions}"],
                }
            if gap < 1.0:
                resolution_notes = resolution_notes + [
                    f"Multiple disease matches found; proceeded with {best['name']} ({best['id']})."
                ]

        resolved = [{"type": "Disease", "id": best["id"], "name": best.get("name"), "score": round(best["score"], 3)}]
        return {"resolved_entities": resolved, "resolution_notes": resolution_notes}

    def route_after_entity_resolution(self, state: ResearchWorkflowState) -> str:
        if not state.get("resolved_entities"):
            return "response_formatting"
        return "graph_query_planning"

    async def graph_query_planning(self, state: ResearchWorkflowState) -> ResearchWorkflowState:
        disease_id = state["resolved_entities"][0]["id"]
        requires_compounds = bool(state.get("requires_compounds"))
        tools = [
            "get_disease_target_graph",
            "retrieve_evidence_chunks",
            "rank_targets",
            "build_graph_payload",
        ]
        if requires_compounds:
            tools.append("get_compounds_for_targets")

        return {
            "graph_query_plan": {
                "module": "disease_target_discovery",
                "primary_disease_id": disease_id,
                "requires_compounds": requires_compounds,
                "tools": tools,
            }
        }

    async def graph_retrieval(self, state: ResearchWorkflowState) -> ResearchWorkflowState:
        disease_id = state["graph_query_plan"]["primary_disease_id"]
        requires_compounds = bool(state["graph_query_plan"].get("requires_compounds"))

        graph_results = await self.tools.get_disease_target_graph(disease_id=disease_id, limit=100)
        graph_payload = await self.tools.build_graph_payload(entity_id=disease_id, depth=1)

        if requires_compounds and not graph_results.get("compounds"):
            protein_ids = [item.get("id") for item in graph_results.get("proteins", []) if item.get("id")]
            gene_ids = [item.get("id") for item in graph_results.get("associated_genes", []) if item.get("id")]
            inferred_compounds = await self.tools.get_compounds_for_targets(
                protein_ids=protein_ids,
                target_gene_ids=gene_ids,
                disease_id=disease_id,
                limit=100,
            )
            if inferred_compounds:
                graph_results["compounds"] = inferred_compounds

        ranking_required = len(graph_results.get("associated_genes", [])) > 1
        return {
            "graph_results": graph_results,
            "graph_payload": graph_payload,
            "ranking_required": ranking_required,
        }

    async def evidence_retrieval(self, state: ResearchWorkflowState) -> ResearchWorkflowState:
        evidence_query = self._build_evidence_query(state)
        disease_id = state.get("graph_query_plan", {}).get("primary_disease_id")
        evidence = await self.tools.retrieve_evidence_chunks(
            query=evidence_query,
            top_k=state.get("top_k", 8),
            disease_id=disease_id,
        )
        updates: ResearchWorkflowState = {"evidence_results": evidence}
        if not evidence:
            updates["errors"] = state.get("errors", []) + ["Insufficient evidence retrieved."]
            updates["ranking_required"] = False
        return updates

    def route_after_evidence(self, state: ResearchWorkflowState) -> str:
        if state.get("ranking_required"):
            return "optional_ranking"
        return "answer_synthesis"

    async def optional_ranking(self, state: ResearchWorkflowState) -> ResearchWorkflowState:
        ranking_results = await self.tools.rank_targets(
            graph_results=state.get("graph_results", {}),
            evidence_results=state.get("evidence_results", []),
        )
        return {"ranking_results": ranking_results}

    async def answer_synthesis(self, state: ResearchWorkflowState) -> ResearchWorkflowState:
        graph_results = state.get("graph_results", {})
        evidence_results = state.get("evidence_results", [])
        ranking_results = state.get("ranking_results", [])
        errors = state.get("errors", [])
        resolution_notes = state.get("resolution_notes", [])
        requires_compounds = bool(state.get("requires_compounds"))

        if not graph_results:
            return {
                "final_answer": "No graph-grounded results available for this query.",
                "citations": [],
            }

        if not evidence_results:
            disease_name = self._safe_string(graph_results.get("disease", {}).get("name"))
            genes = graph_results.get("associated_genes", [])
            proteins = graph_results.get("proteins", [])
            pathways = graph_results.get("pathways", [])
            compounds = graph_results.get("compounds", [])
            compound_signals = graph_results.get("compound_signals", [])

            top_compounds = [
                self._safe_string(item.get("name")) or self._safe_string(item.get("id"))
                for item in compounds[:5]
                if self._safe_string(item.get("name")) or self._safe_string(item.get("id"))
            ]
            compound_text = ", ".join(top_compounds) if top_compounds else "none surfaced in this graph slice"

            compound_note = ""
            if requires_compounds:
                if compound_signals:
                    top_signal_targets = ", ".join(
                        self._safe_string(item.get("target_gene_symbol")) or self._safe_string(item.get("target_gene_id"))
                        for item in compound_signals[:5]
                        if self._safe_string(item.get("target_gene_symbol")) or self._safe_string(item.get("target_gene_id"))
                    )
                    compound_note = (
                        f" Known-drug target signals were detected from ChEMBL/Open Targets for {len(compound_signals)} "
                        f"targets (examples: {top_signal_targets or 'n/a'}), but explicit compound-to-target edges are limited "
                        "in this graph snapshot."
                    )
                elif not compounds:
                    compound_note = " No explicit compound links were found for the resolved disease targets in this graph snapshot."

            note_text = f" Notes: {' '.join(resolution_notes)}" if resolution_notes else ""
            return {
                "final_answer": (
                    f"For {disease_name or 'the requested disease'}, the graph currently shows "
                    f"{len(genes)} candidate genes, {len(proteins)} proteins, {len(pathways)} pathways, "
                    f"and {len(compounds)} linked compounds (examples: {compound_text})."
                    f"{compound_note} Evidence chunk retrieval returned no supporting records, so treat this as graph-only guidance "
                    f"until evidence indexing is expanded.{note_text}"
                ),
                "citations": [],
            }

        if self.reasoner:
            system_prompt = (
                "You are a biomedical research assistant. Use only retrieved context. "
                "Never use parametric memory alone. If evidence is weak, state limitations."
            )
            user_prompt = (
                "Use the JSON context below to answer the user query.\n"
                "Required sections: summary, candidate targets, evidence limits, citations.\n\n"
                f"User Query: {state.get('user_query', '')}\n"
                f"Context: {json.dumps({'graph': graph_results, 'evidence': evidence_results, 'ranking': ranking_results})}"
            )
            try:
                llm_response = await self.reasoner.ainvoke(
                    [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ]
                )
                final_answer = llm_response.content if hasattr(llm_response, "content") else str(llm_response)
            except Exception as exc:
                errors = errors + [f"LLM synthesis failed: {exc}"]
                final_answer = self._fallback_answer(
                    graph_results=graph_results,
                    evidence_results=evidence_results,
                    ranking_results=ranking_results,
                    errors=errors,
                    resolution_notes=resolution_notes,
                )
        else:
            final_answer = self._fallback_answer(
                graph_results=graph_results,
                evidence_results=evidence_results,
                ranking_results=ranking_results,
                errors=errors,
                resolution_notes=resolution_notes,
            )

        citations = [
            {"id": item.get("id"), "source": item.get("source")}
            for item in evidence_results
            if item.get("id")
        ]

        return {
            "final_answer": final_answer,
            "citations": citations,
            "errors": errors,
        }

    async def response_formatting(self, state: ResearchWorkflowState) -> ResearchWorkflowState:
        if not state.get("final_answer"):
            if state.get("errors"):
                return {
                    "final_answer": "Workflow ended with errors: " + "; ".join(state["errors"]),
                }
            return {"final_answer": "No answer could be generated."}
        return {}

    @staticmethod
    def _fallback_answer(
        graph_results: dict[str, Any],
        evidence_results: list[dict[str, Any]],
        ranking_results: list[dict[str, Any]],
        errors: list[str],
        resolution_notes: list[str] | None = None,
    ) -> str:
        disease_name = graph_results.get("disease", {}).get("name", "unknown disease")
        candidate_count = len(graph_results.get("associated_genes", []))
        top_ranked = ranking_results[0]["gene_symbol"] if ranking_results and ranking_results[0].get("gene_symbol") else "n/a"
        compound_count = len(graph_results.get("compounds", []))
        evidence_count = len(evidence_results)
        notes = f" Limitations: {'; '.join(errors)}" if errors else ""
        resolution = f" Resolution notes: {' '.join(resolution_notes)}" if resolution_notes else ""
        return (
            f"Disease: {disease_name}. Candidate genes: {candidate_count}. "
            f"Top-ranked target: {top_ranked}. Linked compounds: {compound_count}. "
            f"Supporting evidence chunks: {evidence_count}.{notes}{resolution}"
        )

    def _build_evidence_query(self, state: ResearchWorkflowState) -> str:
        normalized = state.get("normalized_query", "")
        disease_name = self._safe_string(state.get("graph_results", {}).get("disease", {}).get("name"))
        requires_compounds = bool(state.get("requires_compounds"))

        parts: list[str] = []
        for value in [normalized, disease_name]:
            if value:
                parts.append(value)
        if requires_compounds:
            parts.extend(["chembl", "known drug", "target disease association"])
        else:
            parts.append("target disease association")

        deduped: list[str] = []
        seen: set[str] = set()
        for part in parts:
            key = part.lower().strip()
            if key and key not in seen:
                seen.add(key)
                deduped.append(part)
        return " ".join(deduped)

    @classmethod
    def _build_disease_search_candidates(cls, query: str) -> list[str]:
        normalized = cls._normalize_text(query)
        cleaned = re.sub(r"[^a-z0-9:_\-\s]", " ", normalized)
        cleaned = " ".join(cleaned.split())

        reduced_terms = [term for term in cleaned.split() if len(term) > 2 and term not in cls.QUERY_STOPWORDS]
        reduced_query = " ".join(reduced_terms).strip()

        candidates: list[str] = []
        phrase_matches = re.findall(
            r"([a-z0-9:_\-]+(?:\s+[a-z0-9:_\-]+){0,3}\s+(?:disease|cancer|carcinoma|syndrome|disorder|infection))",
            cleaned,
        )
        cleaned_phrases: list[str] = []
        for phrase in phrase_matches:
            phrase_terms = phrase.split()
            while phrase_terms and phrase_terms[0] in cls.QUERY_STOPWORDS:
                phrase_terms = phrase_terms[1:]
            value = " ".join(phrase_terms).strip()
            if value:
                cleaned_phrases.append(value)

        for alias, canonical in cls.DISEASE_ALIASES.items():
            if alias in cleaned and canonical not in candidates:
                candidates.append(canonical)

        for value in [*cleaned_phrases, reduced_query]:
            if value and value not in candidates:
                candidates.append(value)

        if not candidates and normalized:
            candidates = [normalized]
        return candidates[:8]

    @classmethod
    def _is_alias_candidate(cls, candidate: str, original_query: str) -> bool:
        normalized_candidate = cls._normalize_text(candidate)
        normalized_query = cls._normalize_text(original_query)
        return any(
            alias in normalized_query and canonical == normalized_candidate
            for alias, canonical in cls.DISEASE_ALIASES.items()
        )

    @classmethod
    def _score_disease_hit(
        cls,
        original_query: str,
        candidate: str,
        row: dict[str, Any],
        candidate_rank: int,
        alias_boost: float,
    ) -> float:
        phrase_score = float(row.get("phrase_score") or 0.0)
        token_hits = float(row.get("token_hits") or 0.0)
        synonym_hit = float(row.get("synonym_hit") or 0.0)

        row_name = cls._normalize_text(cls._safe_string(row.get("name")))
        row_id = cls._normalize_text(cls._safe_string(row.get("id")))
        normalized_candidate = cls._normalize_text(candidate)
        normalized_query = cls._normalize_text(original_query)

        query_terms = cls._query_terms(normalized_query)
        row_terms = cls._query_terms(row_name)
        overlap = len(query_terms & row_terms) / max(len(query_terms), 1)

        exact_match = 1.0 if row_name == normalized_candidate or row_id == normalized_candidate else 0.0
        starts_with = 1.0 if row_name.startswith(normalized_candidate) and normalized_candidate else 0.0

        return (
            phrase_score * 3.2
            + token_hits * 1.1
            + synonym_hit * 2.0
            + overlap * 2.0
            + exact_match * 2.0
            + starts_with * 0.5
            + alias_boost
            - (candidate_rank * 0.05)
        )

    @classmethod
    def _query_terms(cls, text: str) -> set[str]:
        tokens = {token for token in re.findall(r"[a-z0-9:_-]+", cls._normalize_text(text)) if len(token) > 2}
        return {token for token in tokens if token not in cls.QUERY_STOPWORDS}

    @staticmethod
    def _normalize_text(value: str) -> str:
        return " ".join(value.lower().split())

    @staticmethod
    def _safe_string(value: Any) -> str:
        return value if isinstance(value, str) else ""
