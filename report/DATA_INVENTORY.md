# Data Inventory — Vu Thanh Danh Day 07

| # | File | Category | Language | Owner | Character count | PII |
|---|---|---|---|---|---:|---|
| 1 | `python_intro.txt` | programming | en | Python / AI study notes | 1,944 | no |
| 2 | `vector_store_notes.md` | vector_store | en | Group RAG notes | 2,123 | no |
| 3 | `rag_system_design.md` | rag_design | en | Internal knowledge assistant scenario | 2,391 | no |
| 4 | `customer_support_playbook.txt` | support | en | Support operations scenario | 1,692 | no |
| 5 | `chunking_experiment_report.md` | chunking | en | Group experiment summary | 1,987 | no |
| 6 | `vi_retrieval_notes.md` | retrieval | vi | Vietnamese retrieval notes | 1,667 | no |

## Metadata schema

| Field | Meaning | Why useful |
|---|---|---|
| `source` | Local source file path | Shows evidence source for retrieved chunks |
| `category` | Main document topic | Enables metadata filtering by domain |
| `language` | `en` or `vi` | Helps route Vietnamese queries to Vietnamese documents |
| `owner` | Source owner / scenario owner | Helps debugging and source attribution |
| `doc_type` | technical note, playbook, design note, etc. | Separates playbooks from design notes and experiments |
| `pii` | Whether personal data exists | Supports safe retrieval and compliance review |
