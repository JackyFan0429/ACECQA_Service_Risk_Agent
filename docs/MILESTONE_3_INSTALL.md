# Milestone 3 — Mac setup and live validation

These steps assume your existing project folder is named `acecqa-risk-agent02` and its `.venv` already works for Milestone 2.

## A. Apply the patch

Unzip the Milestone 3 patch and copy its contents into the root of `acecqa-risk-agent02`, allowing files with the same path to be replaced.

Then:

```bash
cd /Users/jackymini/Downloads/acecqa-risk-agent02
source .venv/bin/activate
pip install -e ".[dev]"
```

## B. Confirm offline regression tests

```bash
pytest -q
```

Expected:

```text
19 passed
```

## C. Build the real official policy corpus

```bash
python scripts/ingest_policy.py
```

The script fetches only the ACECQA URLs listed in:

```text
data/policy/sources.json
```

Then validate the generated corpus:

```bash
python scripts/check_policy_corpus.py
```

Expected ending:

```text
Corpus integrity: PASS
```

The exact number of chunks can change when ACECQA edits its pages; the test does not assume a fixed count.

## D. Test retrieval without using the OpenAI API

```bash
python demo_policy_search.py \
  "What should a regulatory authority consider before deciding how to respond to a compliance issue?"
```

Look for relevant results from regulatory-authority/compliance sections and official `acecqa.gov.au` URLs.

Also test:

```bash
python demo_policy_search.py \
  "What does Working Towards NQS mean?"
```

## E. Run one live Agent policy query

Ensure your key is available:

```bash
python -c "import os; print('OPENAI_API_KEY set:', bool(os.getenv('OPENAI_API_KEY')))"
```

Then:

```bash
python demo_agent.py \
  "What does a Working Towards NQS rating mean?" \
  --show-trace
```

Expected tool:

```text
search_policy
```

The output should also contain a `Policy sources` section with one or more `POL-...` chunk IDs and official ACECQA URLs.

## F. Run the key two-source acceptance case

```bash
python demo_agent.py \
  "Find the 5 highest-risk rural Centre-Based Care services in Queensland and explain what the relevant regulatory authority should consider before deciding how to respond." \
  --show-trace
```

Expected tools include both:

```text
find_high_risk_services
search_policy
```

The risk ranking must still come from the deterministic analytics tool. Policy retrieval should add regulatory context, not change the ranking.

## G. Run Milestone 3 smoke tests

First inspect the cases at zero API cost:

```bash
python run_m3_smoke_tests.py --list
```

Run the most important combined case:

```bash
python run_m3_smoke_tests.py --case M3-04
```

If it passes, run the complete eight-case suite:

```bash
python run_m3_smoke_tests.py
```

Acceptance rule:

```text
>= 7/8 PASS
and
M3-02, M3-04, M3-05, M3-07, M3-08 all PASS
```

Results are saved under:

```text
evals/m3_results/YYYYMMDD_HHMMSS/
```

Send `summary.md` first. If any case fails, also send only the corresponding `M3-XX_raw.json` file(s).
