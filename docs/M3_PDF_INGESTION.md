# Milestone 3 - PDF ingestion fallback

ACECQA may return HTTP 403 to scripted HTML requests. Treat this as an access constraint rather than attempting to bypass it.

## Recommended workflow

1. In Safari/Chrome, open ACECQA's **Guide to the NQF** page.
2. Under **Accessing the Guide**, download the official **Full version** PDF.
3. Keep the PDF outside Git if desired; the generated JSONL corpus is the runtime artifact.
4. Install the updated policy dependencies:

```bash
pip install -e ".[dev]"
```

5. Build the corpus from the local official PDF:

```bash
python scripts/ingest_policy.py --pdf ~/Downloads/<your-downloaded-guide>.pdf
```

6. Validate:

```bash
python scripts/check_policy_corpus.py
```

Expected ending:

```text
Corpus integrity: PASS
```

7. Test retrieval:

```bash
python demo_policy_search.py \
  "What should a regulatory authority consider before deciding how to respond to a compliance issue?"
```

Then:

```bash
python demo_policy_search.py \
  "What does Working Towards NQS mean?"
```

## Why PDF-first is better here

- It uses ACECQA's official downloadable resource instead of fighting anti-bot controls.
- It snapshots a specific policy version for reproducible evaluation.
- It avoids Playwright/Selenium and keeps the project lightweight.
- The Guide is one coherent source containing NQS, assessment/rating, operational requirements, and regulatory authority powers.
- The corpus keeps the official source URL and PDF page number in every chunk.

## Important limitation

The Guide to the NQF is official guidance, not legal advice. The National Law and Regulations take precedence. This Milestone 3 corpus is therefore for policy grounding and decision support, not automated legal determination.
