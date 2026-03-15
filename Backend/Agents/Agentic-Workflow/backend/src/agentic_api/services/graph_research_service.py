from __future__ import annotations

from collections import Counter
import re
from typing import Any

from agentic_api.db.neo4j import Neo4jClient


class GraphResearchService:
    def __init__(self, neo4j_client: Neo4jClient) -> None:
        self.neo4j = neo4j_client

    async def search_disease(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        tokens = self._query_tokens(query)
        return await self.neo4j.run_query(
            """
            WITH toLower($query) AS query_text, $tokens AS tokens
            MATCH (d:Disease)
            WITH d,
                 toLower(coalesce(d['name'], '')) AS name_text,
                 toLower(coalesce(d['external_id'], d['node_id'], '')) AS id_text,
                 toLower(coalesce(d['synonyms'], '')) AS synonyms_text,
                 query_text,
                 tokens
            WITH d, name_text, id_text, synonyms_text, query_text,
                 size(
                   [
                     token IN tokens
                     WHERE name_text CONTAINS token
                        OR id_text CONTAINS token
                        OR synonyms_text CONTAINS token
                   ]
                 ) AS token_hits,
                 CASE
                   WHEN name_text = query_text OR id_text = query_text THEN 4
                   WHEN synonyms_text CONTAINS query_text THEN 3
                   WHEN name_text STARTS WITH query_text OR id_text STARTS WITH query_text THEN 2
                   WHEN name_text CONTAINS query_text OR id_text CONTAINS query_text THEN 1
                   ELSE 0
                 END AS phrase_score
            WHERE name_text CONTAINS query_text
               OR id_text CONTAINS query_text
               OR synonyms_text CONTAINS query_text
               OR token_hits > 0
            RETURN DISTINCT coalesce(d['external_id'], d['node_id']) AS id,
                            coalesce(d['name'], coalesce(d['external_id'], d['node_id'])) AS name,
                            coalesce(d['external_id'], d['node_id']) AS ontology_id,
                            token_hits,
                            phrase_score,
                            CASE WHEN synonyms_text CONTAINS query_text THEN 1 ELSE 0 END AS synonym_hit
            ORDER BY phrase_score DESC, synonym_hit DESC, token_hits DESC, name
            LIMIT $limit
            """,
            {"query": query, "tokens": tokens, "limit": limit},
        )

    async def search_gene(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        return await self.neo4j.run_query(
            """
            MATCH (g:Gene)
            WHERE
              (
                toLower(coalesce(g['name'], '')) CONTAINS toLower($query)
                OR toLower(coalesce(g['external_id'], g['node_id'], '')) CONTAINS toLower($query)
                OR toLower(coalesce(g['synonyms'], '')) CONTAINS toLower($query)
              )
            RETURN DISTINCT coalesce(g['external_id'], g['node_id']) AS id,
                            g['name'] AS symbol,
                            g['name'] AS name
            ORDER BY symbol
            LIMIT $limit
            """,
            {"query": query, "limit": limit},
        )

    async def search_protein(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        return await self.neo4j.run_query(
            """
            MATCH (p:Protein)
            WHERE (
                toLower(coalesce(p['name'], '')) CONTAINS toLower($query)
                OR toLower(coalesce(p['external_id'], p['node_id'], '')) CONTAINS toLower($query)
                OR toLower(coalesce(p['synonyms'], '')) CONTAINS toLower($query)
              )
            RETURN DISTINCT coalesce(p['external_id'], p['node_id']) AS id,
                            p['name'] AS name
            ORDER BY name
            LIMIT $limit
            """,
            {"query": query, "limit": limit},
        )

    async def get_disease_target_graph(self, disease_id: str, limit: int = 100) -> dict[str, Any]:
        disease = await self._get_disease_by_id(disease_id=disease_id)
        genes = await self._get_genes_for_disease(disease_id=disease_id, limit=limit)
        gene_ids = [g["id"] for g in genes if g.get("id")]
        protein_seed_gene_ids = gene_ids[:25]

        proteins = await self._get_proteins_for_genes(gene_ids=protein_seed_gene_ids, limit=limit)
        protein_ids = [p["id"] for p in proteins if p.get("id")]

        partners = await self._get_interaction_partners(protein_ids=protein_ids, limit=limit)
        pathways = await self.get_pathway_context_for_proteins(protein_ids=protein_ids, limit=limit)
        compounds = await self.get_compounds_for_targets(
            protein_ids=protein_ids,
            target_gene_ids=gene_ids,
            disease_id=disease_id,
            limit=limit,
        )
        compound_signals = await self._get_known_drug_compound_signals(disease_id=disease_id, limit=limit)

        evidence_count, source_breakdown = await self._get_disease_evidence_breakdown(disease_id=disease_id)

        return {
            "disease": disease,
            "associated_genes": genes,
            "proteins": proteins,
            "interaction_partners": partners,
            "pathways": pathways,
            "compounds": compounds,
            "compound_signals": compound_signals,
            "evidence_summary": {
                "evidence_count": evidence_count,
                "source_breakdown": source_breakdown,
                "known_drug_signal_count": len(compound_signals),
            },
        }

    async def get_protein_neighbors(self, protein_id: str, depth: int = 2, limit: int = 120) -> dict[str, Any]:
        return await self.graph_neighborhood(entity_id=protein_id, depth=depth, limit=limit)

    async def get_pathway_context_for_proteins(self, protein_ids: list[str], limit: int = 100) -> list[dict[str, Any]]:
        if not protein_ids:
            return []

        direct_rows = await self.neo4j.run_query(
            """
            UNWIND $protein_ids AS protein_id
            MATCH (p:Protein)
            WHERE coalesce(p['external_id'], p['node_id']) = protein_id
            MATCH (p)-[r:RELATED_TO|HAS_RELATION_FACT]-(pathway:Pathway)
            RETURN DISTINCT coalesce(pathway['external_id'], pathway['node_id']) AS id,
                            coalesce(pathway['name'], coalesce(pathway['external_id'], pathway['node_id'])) AS name,
                            coalesce(r['score'], 0.0) AS pathway_score
            ORDER BY pathway_score DESC, name
            LIMIT $limit
            """,
            {"protein_ids": protein_ids, "limit": limit},
        )
        return self._merge_unique_rows(direct_rows, limit=limit)

    async def get_compounds_for_targets(
        self,
        protein_ids: list[str],
        target_gene_ids: list[str] | None = None,
        disease_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        compounds: list[dict[str, Any]] = []

        if protein_ids:
            direct_rows = await self.neo4j.run_query(
                """
                UNWIND $protein_ids AS protein_id
                MATCH (p:Protein)
                WHERE coalesce(p['external_id'], p['node_id']) = protein_id
                MATCH (p)-[r:RELATED_TO|HAS_RELATION_FACT]-(compound:Compound)
                RETURN DISTINCT coalesce(compound['external_id'], compound['node_id']) AS id,
                                coalesce(compound['name'], coalesce(compound['external_id'], compound['node_id'])) AS name,
                                coalesce(r['score'], 0.0) AS activity_score,
                                coalesce(r['source'], 'graph') AS source
                ORDER BY activity_score DESC, name
                LIMIT $limit
                """,
                {"protein_ids": protein_ids, "limit": limit},
            )
            compounds = self._merge_unique_rows(direct_rows, limit=limit)

        if not compounds and target_gene_ids and protein_ids:
            gene_rows = await self.neo4j.run_query(
                """
                UNWIND $gene_ids AS gene_id
                MATCH (g:Gene)
                WHERE coalesce(g['external_id'], g['node_id']) = gene_id
                OPTIONAL MATCH (g)-[r1:RELATED_TO|HAS_RELATION_FACT]-(compound:Compound)
                OPTIONAL MATCH (g)-[:RELATED_TO|HAS_RELATION_FACT]-(p:Protein)-[r2:RELATED_TO|HAS_RELATION_FACT]-(compound2:Compound)
                WITH g,
                     collect(DISTINCT {
                        id: coalesce(compound['external_id'], compound['node_id']),
                        name: coalesce(compound['name'], coalesce(compound['external_id'], compound['node_id'])),
                        activity_score: coalesce(r1['score'], 0.0),
                        source: coalesce(r1['source'], 'graph')
                     }) +
                     collect(DISTINCT {
                        id: coalesce(compound2['external_id'], compound2['node_id']),
                        name: coalesce(compound2['name'], coalesce(compound2['external_id'], compound2['node_id'])),
                        activity_score: coalesce(r2['score'], 0.0),
                        source: coalesce(r2['source'], 'graph')
                     }) AS candidates
                UNWIND candidates AS candidate
                WITH candidate
                WHERE candidate.id IS NOT NULL
                RETURN DISTINCT candidate.id AS id,
                                candidate.name AS name,
                                candidate.activity_score AS activity_score,
                                candidate.source AS source
                ORDER BY activity_score DESC, name
                LIMIT $limit
                """,
                {"gene_ids": target_gene_ids, "limit": limit},
            )
            compounds = self._merge_unique_rows(gene_rows, limit=limit)

        if compounds:
            return compounds[:limit]

        if disease_id:
            return await self._get_known_drug_compound_signals(disease_id=disease_id, limit=limit)
        return []

    async def graph_neighborhood(self, entity_id: str, depth: int = 2, limit: int = 120) -> dict[str, Any]:
        bounded_depth = min(max(depth, 1), 3)
        query = f"""
        MATCH (center)
        WHERE coalesce(center['external_id'], center['node_id']) = $entity_id
        OPTIONAL MATCH path = (center)-[:RELATED_TO|HAS_RELATION_FACT*1..{bounded_depth}]-(neighbor)
        RETURN path
        LIMIT $limit
        """
        rows = await self.neo4j.run_query(query, {"entity_id": entity_id, "limit": limit})

        nodes: dict[str, dict[str, Any]] = {}
        edges: dict[str, dict[str, Any]] = {}
        for row in rows:
            path = row.get("path")
            if not path:
                continue
            for node in path.get("nodes", []):
                node_id = node.get("id")
                if node_id:
                    nodes[node_id] = {
                        "id": node_id,
                        "label": node.get("properties", {}).get("name", node_id),
                        "type": (node.get("labels") or ["Entity"])[-1],
                        "properties": node.get("properties", {}),
                    }
            for rel in path.get("relationships", []):
                edge_id = rel.get("id")
                source = rel.get("properties", {}).get("source_node_id") or rel.get("start_node_id")
                target = rel.get("properties", {}).get("target_node_id") or rel.get("end_node_id")
                if edge_id and source and target:
                    edges[edge_id] = {
                        "id": edge_id,
                        "source": str(source),
                        "target": str(target),
                        "type": rel.get("type", "RELATED_TO"),
                        "properties": rel.get("properties", {}),
                    }

        return {
            "center_id": entity_id,
            "depth": bounded_depth,
            "nodes": list(nodes.values()),
            "edges": list(edges.values()),
        }

    async def search_evidence(self, query_text: str, limit: int = 30, disease_id: str | None = None) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"query_text": query_text, "limit": limit}
        if disease_id:
            params["disease_id"] = disease_id
            return await self.neo4j.run_query(
                """
                MATCH (d:Disease)
                WHERE coalesce(d['external_id'], d['node_id']) = $disease_id
                MATCH (a)-[r:HAS_RELATION_FACT|RELATED_TO]-(d)
                RETURN DISTINCT coalesce(r['relation_id'], elementId(r)) AS id,
                                trim(
                                  coalesce(a['name'], coalesce(a['external_id'], a['node_id'], ''))
                                  + ' '
                                  + coalesce(r['relation_type'], type(r))
                                  + ' '
                                  + coalesce(d['name'], coalesce(d['external_id'], d['node_id'], ''))
                                ) AS text,
                                coalesce(r['source'], r['evidence'], 'graph') AS source,
                                coalesce(r['score'], 0.0) AS confidence_score,
                                r['relation_id'] AS source_record_id
                ORDER BY confidence_score DESC
                LIMIT $limit
                """,
                params,
            )

        return await self.neo4j.run_query(
            """
            MATCH (a)-[r:HAS_RELATION_FACT|RELATED_TO]-(b)
            WHERE
              toLower(coalesce(r['evidence'], '')) CONTAINS toLower($query_text)
              OR toLower(coalesce(r['relation_type'], '')) CONTAINS toLower($query_text)
              OR toLower(coalesce(r['relation_id'], '')) CONTAINS toLower($query_text)
              OR toLower(coalesce(r['payload_json'], '')) CONTAINS toLower($query_text)
              OR toLower(coalesce(a['name'], '')) CONTAINS toLower($query_text)
              OR toLower(coalesce(b['name'], '')) CONTAINS toLower($query_text)
            RETURN DISTINCT coalesce(r['relation_id'], elementId(r)) AS id,
                            trim(
                              coalesce(a['name'], coalesce(a['external_id'], a['node_id'], ''))
                              + ' '
                              + coalesce(r['relation_type'], type(r))
                              + ' '
                              + coalesce(b['name'], coalesce(b['external_id'], b['node_id'], ''))
                            ) AS text,
                            coalesce(r['source'], r['evidence'], 'graph') AS source,
                            coalesce(r['score'], 0.0) AS confidence_score,
                            r['relation_id'] AS source_record_id
            LIMIT $limit
            """,
            params,
        )

    @staticmethod
    def _query_tokens(query: str) -> list[str]:
        raw_tokens = re.findall(r"[a-zA-Z0-9:_-]+", query.lower())
        return [token for token in raw_tokens if len(token) >= 3]

    async def _get_disease_by_id(self, disease_id: str) -> dict[str, Any]:
        rows = await self.neo4j.run_query(
            """
            MATCH (d:Disease)
            WHERE coalesce(d['external_id'], d['node_id']) = $disease_id
            RETURN coalesce(d['external_id'], d['node_id']) AS id,
                   coalesce(d['name'], coalesce(d['external_id'], d['node_id'])) AS name,
                   coalesce(d['external_id'], d['node_id']) AS ontology_id
            LIMIT 1
            """,
            {"disease_id": disease_id},
        )
        return rows[0] if rows else {"id": disease_id, "name": disease_id, "ontology_id": disease_id}

    async def _get_genes_for_disease(self, disease_id: str, limit: int) -> list[dict[str, Any]]:
        direct_rows = await self.neo4j.run_query(
            """
            MATCH (d:Disease)
            WHERE coalesce(d['external_id'], d['node_id']) = $disease_id
            MATCH (d)-[r:RELATED_TO|HAS_RELATION_FACT]-(g:Gene)
            RETURN DISTINCT coalesce(g['external_id'], g['node_id']) AS id,
                            g['name'] AS symbol,
                            g['name'] AS name,
                            coalesce(r['score'], 0.0) AS association_score
            ORDER BY association_score DESC, symbol
            LIMIT $limit
            """,
            {"disease_id": disease_id, "limit": limit},
        )
        return self._merge_unique_rows(direct_rows, limit=limit)

    async def _get_proteins_for_genes(self, gene_ids: list[str], limit: int) -> list[dict[str, Any]]:
        if not gene_ids:
            return []
        return await self.neo4j.run_query(
            """
            UNWIND $gene_ids AS gene_id
            MATCH (g:Gene)
            WHERE coalesce(g['external_id'], g['node_id']) = gene_id
            MATCH (g)-[r:RELATED_TO]-(p:Protein)
            RETURN DISTINCT coalesce(p['external_id'], p['node_id']) AS id,
                            coalesce(p['name'], coalesce(p['external_id'], p['node_id'])) AS name,
                            coalesce(r['score'], 0.0) AS link_score
            ORDER BY link_score DESC, name
            LIMIT $limit
            """,
            {"gene_ids": gene_ids, "limit": limit},
        )

    async def _get_interaction_partners(self, protein_ids: list[str], limit: int) -> list[dict[str, Any]]:
        if not protein_ids:
            return []
        direct_rows = await self.neo4j.run_query(
            """
            UNWIND $protein_ids AS protein_id
            MATCH (p:Protein)
            WHERE coalesce(p['external_id'], p['node_id']) = protein_id
            MATCH (p)-[r:RELATED_TO|HAS_RELATION_FACT]-(partner:Protein)
            WHERE coalesce(partner['external_id'], partner['node_id']) <> protein_id
            RETURN DISTINCT coalesce(partner['external_id'], partner['node_id']) AS id,
                            coalesce(partner['name'], coalesce(partner['external_id'], partner['node_id'])) AS name,
                            coalesce(r['score'], 0.0) AS interaction_score
            ORDER BY interaction_score DESC, name
            LIMIT $limit
            """,
            {"protein_ids": protein_ids, "limit": limit},
        )
        return self._merge_unique_rows(direct_rows, limit=limit)

    async def _get_known_drug_compound_signals(self, disease_id: str, limit: int) -> list[dict[str, Any]]:
        return await self.neo4j.run_query(
            """
            MATCH (g:Gene)-[r:HAS_RELATION_FACT|RELATED_TO]-(d:Disease)
            WHERE coalesce(d['external_id'], d['node_id']) = $disease_id
              AND (
                toLower(coalesce(r['evidence'], '')) CONTAINS 'chembl'
                OR toLower(coalesce(r['payload_json'], '')) CONTAINS 'known_drug'
                OR toLower(coalesce(r['payload_json'], '')) CONTAINS 'chembl'
              )
            RETURN DISTINCT
                'CHEMBL_SIGNAL:' + coalesce(g['external_id'], g['node_id']) AS id,
                'Known-drug evidence (ChEMBL) for target ' + coalesce(g['name'], coalesce(g['external_id'], g['node_id'])) AS name,
                coalesce(r['score'], 0.0) AS activity_score,
                coalesce(r['source'], r['evidence'], 'OpenTargets') AS source,
                true AS inferred,
                coalesce(g['external_id'], g['node_id']) AS target_gene_id,
                coalesce(g['name'], coalesce(g['external_id'], g['node_id'])) AS target_gene_symbol
            ORDER BY activity_score DESC, name
            LIMIT $limit
            """,
            {"disease_id": disease_id, "limit": limit},
        )

    async def _get_disease_evidence_breakdown(self, disease_id: str) -> tuple[int, dict[str, int]]:
        rows = await self.neo4j.run_query(
            """
            MATCH (d:Disease)
            WHERE coalesce(d['external_id'], d['node_id']) = $disease_id
            MATCH ()-[r:HAS_RELATION_FACT|RELATED_TO]-(d)
            RETURN coalesce(r['source'], r['evidence'], 'graph') AS source, count(*) AS evidence_count
            ORDER BY evidence_count DESC
            """,
            {"disease_id": disease_id},
        )
        source_breakdown = {str(row.get("source") or "unknown"): int(row.get("evidence_count") or 0) for row in rows}
        return sum(source_breakdown.values()), source_breakdown

    @staticmethod
    def _merge_unique_rows(rows: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
        merged: dict[str, dict[str, Any]] = {}
        for row in rows:
            row_id = str(row.get("id")) if row.get("id") is not None else ""
            if not row_id:
                continue
            if row_id not in merged:
                merged[row_id] = row
                continue

            current = merged[row_id]
            current_score = float(current.get("activity_score") or current.get("association_score") or current.get("interaction_score") or current.get("link_score") or current.get("pathway_score") or 0.0)
            row_score = float(row.get("activity_score") or row.get("association_score") or row.get("interaction_score") or row.get("link_score") or row.get("pathway_score") or 0.0)
            if row_score > current_score:
                merged[row_id] = row
        return list(merged.values())[:limit]
