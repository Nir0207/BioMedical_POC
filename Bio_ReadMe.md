# Biology Primer For This POC

This document is the minimum biology and biomedical domain context needed before changing the KG pipeline, Cypher layer, backend logic, or UI behavior in this repository.

## What This POC Is Modeling

The project is building a biomedical knowledge graph around a few core entity types:

- `Gene`
- `Protein`
- `Disease`
- `Compound`
- `Pathway`

The graph combines public research datasets so we can:
- connect targets to diseases
- connect genes to proteins and pathways
- connect compounds to targets and mechanisms
- inspect evidence-backed relations in Neo4j

This is not a clinical decision system. It is a research-oriented graph integration and exploration platform.

## Core Biology Concepts

### Gene

A gene is a DNA-level unit that encodes a functional product.

In this project:
- genes usually appear with Ensembl-style identifiers such as `ENSG00000141510`
- genes are commonly linked to diseases, proteins, and pathways

Example:
- `ENSG00000141510` = `TP53`

### Protein

A protein is the functional molecular product usually produced from gene expression.

In this project:
- proteins often use UniProt identifiers such as `UNIPROT:P04637`
- proteins participate in pathways
- proteins are often targets for compounds/drugs

Example:
- `UNIPROT:P04637` is the UniProt protein record for p53

### Disease

A disease node represents a disorder or phenotype concept.

In this project:
- diseases commonly use MONDO or EFO-like identifiers
- diseases connect to genes and proteins through association evidence

Examples:
- `MONDO_0007254` = breast cancer
- `EFO` terms are also present in some source systems

### Compound

A compound is usually a small molecule, drug-like entity, or bioactive chemical.

In this project:
- compounds often use ChEMBL identifiers such as `CHEMBL:CHEMBL25`
- compounds connect to protein targets or mechanism facts

### Pathway

A pathway is a curated biological process or signaling/metabolic route.

In this project:
- pathways mainly come from Reactome
- genes/proteins connect to pathways via membership or participation

## Identifier Systems You Will See

These IDs are critical. Do not casually rewrite them.

- `ENSG...`
  - Ensembl gene identifiers
- `UNIPROT:P...`
  - UniProt protein identifiers
- `MONDO_...`
  - MONDO disease identifiers
- `EFO_...` or `EFO:...`
  - Experimental Factor Ontology identifiers
- `CHEMBL:CHEMBL...`
  - ChEMBL compound identifiers
- Reactome pathway accessions
  - pathway identifiers from Reactome

Production rule:
- preserve source IDs exactly
- do not invent IDs unless there is an explicit normalization rule
- distinguish symbol from identifier

Bad example:
- treating `TP53` as if it were an HGNC identifier

Good example:
- keep `TP53` as a symbol/name and `ENSG00000141510` as the stable ID

## Biology vs Evidence

This graph mixes two kinds of relationships:

### Structural/biological links

These are graph edges such as:
- gene to protein
- gene/protein to pathway
- compound to target

They are usually modeled through `RELATED_TO` with a typed property like `relationship_type`.

### Evidence-backed assertions

These are relation facts such as:
- target disease association evidence
- compound target mechanism evidence

They are often modeled via `HAS_RELATION_FACT`.

This distinction matters:
- some edges describe biology directly
- some edges describe evidence that a relation is supported by a source

## Main Data Sources In This POC

### Open Targets

Used for:
- target entities
- disease entities
- target-disease evidence/association scores

Why it matters:
- it is one of the main drivers of disease-target relationships in the graph

Common things to expect:
- target-disease associations
- evidence source names
- scores

### Reactome

Used for:
- pathway nodes
- protein/gene to pathway membership

Why it matters:
- gives biological process context around genes and proteins

### UniProt

Used for:
- protein entities
- reviewed protein metadata

Why it matters:
- stable protein-level identifiers and annotations

### BioGRID

Used for:
- interaction data, especially gene/protein interaction context

Why it matters:
- expands network neighborhood around molecular entities

### ChEMBL

Used for:
- compound entities
- target-mechanism relationships

Why it matters:
- connects chemistry and pharmacology into the graph

## Common Entity Examples

Use these when sanity-checking graph behavior:

- Gene: `ENSG00000141510` = `TP53`
- Protein: `UNIPROT:P04637`
- Disease: `MONDO_0007254` = breast cancer

These are already useful in this repo’s Query Canvas and graph checks.

## Important Biomedical Relationship Patterns

### Gene -> Disease

This usually means:
- genetic association
- literature support
- animal model evidence
- known drug or evidence aggregation

In this graph, that may appear as:
- `RELATED_TO` with `relationship_type = ASSOCIATED_WITH`
- `HAS_RELATION_FACT` with `relation_type = TARGET_DISEASE_ASSOCIATION`

### Gene -> Protein

This is a structural biology link.

Common meaning:
- the gene encodes the protein product

### Protein/Gene -> Pathway

This means the entity participates in or maps to a biological pathway.

### Compound -> Protein

This means:
- the compound binds/modulates a target
- or there is a mechanism-of-action relation in ChEMBL-derived data

## What To Be Careful About

### 1. Symbol is not ID

Do not confuse:
- `TP53` as a human-readable symbol
with:
- `ENSG00000141510` as the stable entity ID

### 2. Disease ontologies differ

You may see MONDO, EFO, or other ontology identifiers.

Do not assume:
- one disease ID system equals another

Map only when the source explicitly provides a mapping.

### 3. “Association” is not causation

A target-disease association often means evidence-backed relevance, not proof of causal biology or therapeutic success.

### 4. Protein and gene are related but not interchangeable

Some sources are gene-centric.
Some are protein-centric.

Do not collapse them unless the modeling decision explicitly requires it.

### 5. Evidence sources matter

Different evidence channels can support the same pair:
- literature
- genetics
- animal model
- known drug

Preserving evidence provenance is important for auditability.

## Neo4j Modeling Expectations In This Repo

You will commonly see:

- `(:Entity:Gene)`
- `(:Entity:Protein)`
- `(:Entity:Disease)`
- `(:Entity:Compound)`
- `(:Entity:Pathway)`

And relationships such as:

- `[:RELATED_TO]`
  - semantic meaning is usually carried in `relationship_type`
- `[:HAS_RELATION_FACT]`
  - evidence-backed or assertion-like relation facts

Key implication:
- relationship semantics are sometimes in properties, not only in the raw Neo4j relationship type

## Querying Guidance

When writing Cypher for this repo:

- prefer matching by `node_id`
- always verify the actual label combination in the graph
- do not assume disease/gene/protein IDs without checking source format
- if you need graph-renderable output for the UI, return `path` objects

Good:
```cypher
MATCH p = (:Entity:Gene {node_id: "ENSG00000141510"})-[:RELATED_TO]-(:Entity:Disease {node_id: "MONDO_0007254"})
RETURN p
LIMIT 25
```

Risky:
```cypher
MATCH (g {name: "TP53"})-[]-(d {name: "breast cancer"})
RETURN g, d
```

The second form is weaker because names are less stable than IDs.

## Practical Checks Before You Change Anything

Before modifying ETL, backend, or UI logic, check:

1. Is this source gene-centric, protein-centric, or disease-centric?
2. Is the field I am using a stable ID, symbol, synonym, or display name?
3. Is the relation structural biology or evidence-backed assertion?
4. Am I preserving provenance and source context?
5. Will this change collapse distinct biological concepts incorrectly?

## Good First Queries To Understand The Graph

### TP53 to breast cancer
```cypher
MATCH p = (:Entity:Gene {node_id: "ENSG00000141510"})-[:RELATED_TO]-(:Entity:Disease {node_id: "MONDO_0007254"})
RETURN p
LIMIT 25
```

### TP53 disease evidence facts
```cypher
MATCH p = (:Entity:Gene {node_id: "ENSG00000141510"})-[:HAS_RELATION_FACT]-(:Entity:Disease {node_id: "MONDO_0007254"})
RETURN p
LIMIT 25
```

### TP53 protein mapping
```cypher
MATCH p = (:Entity:Gene {node_id: "ENSG00000141510"})-[:RELATED_TO]-(:Entity:Protein {node_id: "UNIPROT:P04637"})
RETURN p
LIMIT 10
```

## Recommended Working Mindset

Treat this POC like a research graph system with production discipline:

- IDs first
- provenance always
- no silent biological assumptions
- no collapsing gene/protein/disease semantics casually
- optimize for auditability and correctness before convenience
