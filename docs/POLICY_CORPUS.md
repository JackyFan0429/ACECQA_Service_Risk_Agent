# Policy Corpus Design

## Source policy

Milestone 3 uses a curated allow-list of official ACECQA pages rather than arbitrary web search. The source manifest is `data/policy/sources.json`.

The initial source set covers:

- Guide to the National Quality Framework overview
- National Quality Standard
- Assessment and rating process
- Guide Section 3: NQS and Assessment/Rating
- Rating system
- Guide Section 5: Regulatory Authority Powers
- Compliance tools
- Enforceable undertakings
- Functions and powers of regulatory authorities
- National Regulations landing/reference page

This corpus is designed around the product questions the Agent needs to answer, not around ingesting every document on the ACECQA website.

## Legal/source hierarchy

The retrieval metadata distinguishes guidance from legislation references. The Agent prompt also enforces two rules:

1. The Guide to the NQF is guidance and is not legal advice.
2. The National Law and Regulations take precedence over guidance.

The first milestone does not attempt to provide jurisdiction-specific legal advice.

## Ingestion

```bash
python scripts/ingest_policy.py
```

The script:

1. reads the official source allow-list;
2. downloads each page;
3. removes navigation/script/style noise;
4. preserves heading context;
5. chunks paragraphs/list/table text by section;
6. assigns stable source-based chunk IDs;
7. records source URL, type, topic tags and retrieval timestamp;
8. writes a local JSONL corpus.

Generated page text should be refreshed before an important demo because official guidance may change.

## Retrieval

`PolicyRepository` builds an in-memory BM25 index. Source title and section headings receive extra lexical weight, and curated keywords/topics help the tool distinguish concepts such as:

- Working Towards NQS
- assessment and rating
- QIP / continuous improvement
- regulatory powers
- proportionality
- risk to children
- compliance history
- compliance tools
- legal hierarchy

`search_policy()` returns the top grounded passages; the LLM explains them but does not choose the passage contents itself.

## Citation integrity

A policy evidence object carries `policy_chunk_ids`. At runtime:

1. the application reads every chunk ID actually returned by `search_policy`;
2. the final answer is rejected if it cites an ID that was not retrieved;
3. the application resolves title, URL and section from the tool trace;
4. model-generated URLs are not trusted as the source of truth.

This is intentionally stronger than prompting the LLM to "include citations".
