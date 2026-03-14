# Neo4j Cypher Query Library

This folder stores reusable Cypher queries grouped by purpose so graph operations, QA, and analysis stay organized over time.

## Categories

- `00_constraints/`: schema constraints and indexes
- `01_load_validation/`: post-load validation and integrity checks
- `02_quality_checks/`: duplicate, orphan, and distribution checks
- `03_exploration/`: common graph exploration and analyst-facing queries
- `04_subgraphs/`: reusable subgraph extraction patterns
- `05_maintenance/`: cleanup and administrative operations

## Naming

- One file per query or tightly related query set
- Prefix files numerically inside each category to keep execution order obvious
- Keep parameters explicit in comments at the top of each file

## Notes

- The current KG model uses:
  - nodes labeled `:Entity` plus a domain label such as `:Gene`, `:Protein`, `:Disease`, `:Pathway`, `:Compound`
  - graph edges typed as `:RELATED_TO` with the semantic type stored in `relationship_type`
  - relation facts typed as `:HAS_RELATION_FACT`
