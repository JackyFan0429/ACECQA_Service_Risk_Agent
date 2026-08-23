from pathlib import Path

from acecqa_agent.rag.policy_repository import PolicyRepository
from acecqa_agent.schemas import PolicySearchInput

FIXTURE = Path(__file__).parent / "fixtures" / "policy_chunks.jsonl"


def test_policy_repository_routes_regulatory_response_query():
    repo = PolicyRepository(FIXTURE)
    results = repo.search(
        "What should regulators consider before deciding a proportionate response to a risky service?",
        top_k=2,
    )
    assert results
    assert results[0]["source_id"] == "regulatory_authority_powers"


def test_policy_repository_supports_topic_filter():
    repo = PolicyRepository(FIXTURE)
    results = repo.search("Working Towards NQS improvement", top_k=3, topic="working_towards_nqs")
    assert len(results) == 1
    assert results[0]["chunk_id"] == "POL-assessment_rating_process-0001"


def test_policy_repository_exposes_traceable_metadata():
    repo = PolicyRepository(FIXTURE)
    result = repo.search("ACECQA national regulator", top_k=1)[0]
    assert result["chunk_id"].startswith("POL-")
    assert result["source_url"].startswith("https://www.acecqa.gov.au/")
    assert result["source_retrieved_at"]


def test_default_policy_corpus_path_uses_shared_project_root(monkeypatch, tmp_path):
    # Regression guard for Docker/non-editable installs: policy retrieval must not
    # infer the repository root from policy_repository.__file__ under site-packages.
    import acecqa_agent.rag.policy_repository as policy_repository

    monkeypatch.delenv("ACECQA_POLICY_CORPUS_PATH", raising=False)
    monkeypatch.setattr(policy_repository, "PROJECT_ROOT", tmp_path)

    assert policy_repository._default_corpus_path() == (
        tmp_path / "data" / "policy" / "policy_chunks.jsonl"
    )
