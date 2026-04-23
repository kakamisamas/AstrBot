from astrbot.core.provider.sources.bailian_rerank_source import BailianRerankProvider


def test_qwen3_rerank_build_payload_uses_input_object():
    provider = BailianRerankProvider.__new__(BailianRerankProvider)
    provider.model = "qwen3-rerank"
    provider.instruct = ""
    provider.return_documents = False

    payload = provider._build_payload(
        query="Apple",
        documents=["apple", "banana"],
        top_n=None,
    )

    assert payload == {
        "model": "qwen3-rerank",
        "input": {
            "query": "Apple",
            "documents": ["apple", "banana"],
        },
    }


def test_qwen3_rerank_build_payload_keeps_instruct_and_top_n_compatible():
    provider = BailianRerankProvider.__new__(BailianRerankProvider)
    provider.model = "qwen3-rerank"
    provider.instruct = "Rank documents by semantic relevance."
    provider.return_documents = False

    payload = provider._build_payload(
        query="Apple",
        documents=["apple", "banana"],
        top_n=1,
    )

    assert payload == {
        "model": "qwen3-rerank",
        "input": {
            "query": "Apple",
            "documents": ["apple", "banana"],
        },
        "parameters": {
            "top_n": 1,
        },
        "instruct": "Rank documents by semantic relevance.",
    }
