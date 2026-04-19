import json
from unittest.mock import MagicMock

import pytest

from astrbot.core.tools import web_search_tools as module


def _make_context(provider_settings: dict):
    context = MagicMock()
    context.context = MagicMock()
    context.context.event = MagicMock()
    context.context.event.unified_msg_origin = "test:private:session"
    cfg = {"provider_settings": provider_settings}
    context.context.context = MagicMock()
    context.context.context.get_config.return_value = cfg
    return context


def test_extract_kimi_search_results_collects_nested_records():
    payload = {
        "query": "latest kimi",
        "search_results": [
            {
                "title": "Moonshot News",
                "url": "https://platform.moonshot.cn/news/1",
                "snippet": "Latest Kimi update.",
            },
            {
                "name": "Kimi Docs",
                "link": "https://platform.kimi.com/docs/guide/use-web-search",
                "content": "Official Kimi web search guide.",
            },
        ],
        "meta": {"search_tokens": 128},
    }

    results = module._extract_kimi_search_results(payload)

    assert results == [
        module.SearchResult(
            title="Moonshot News",
            url="https://platform.moonshot.cn/news/1",
            snippet="Latest Kimi update.",
            favicon=None,
        ),
        module.SearchResult(
            title="Kimi Docs",
            url="https://platform.kimi.com/docs/guide/use-web-search",
            snippet="Official Kimi web search guide.",
            favicon=None,
        ),
    ]


@pytest.mark.asyncio
async def test_kimi_web_search_tool_builds_builtin_web_search_request(monkeypatch):
    context = _make_context(
        {
            "websearch_kimi_api_key": ["test-kimi-key"],
            "websearch_kimi_api_base": "https://api.moonshot.cn/v1",
            "websearch_kimi_model": "kimi-k2.5",
        }
    )
    captured = {}

    async def fake_search(provider_settings, payload):
        captured["provider_settings"] = provider_settings
        captured["payload"] = payload
        return [
            module.SearchResult(
                title="Result A",
                url="https://example.com/a",
                snippet="Snippet A",
            )
        ]

    monkeypatch.setattr(module, "_kimi_search", fake_search)

    result = await module.KimiWebSearchTool().call(context, query="Kimi 搜索怎么接入")

    assert captured["provider_settings"]["websearch_kimi_api_key"] == ["test-kimi-key"]
    assert captured["payload"] == {
        "model": "kimi-k2.5",
        "messages": [{"role": "user", "content": "Kimi 搜索怎么接入"}],
        "tools": [{"type": "builtin_function", "function": {"name": "$web_search"}}],
        "thinking": {"type": "disabled"},
        "stream": False,
    }
    parsed = json.loads(result)
    assert parsed["results"][0]["title"] == "Result A"
    assert parsed["results"][0]["url"] == "https://example.com/a"


@pytest.mark.asyncio
async def test_kimi_web_search_tool_requires_api_key():
    context = _make_context(
        {
            "websearch_kimi_api_key": [],
            "websearch_kimi_api_base": "https://api.moonshot.cn/v1",
            "websearch_kimi_model": "kimi-k2.5",
        }
    )

    result = await module.KimiWebSearchTool().call(context, query="Kimi")

    assert result == "Error: Kimi API key is not configured in AstrBot."


@pytest.mark.asyncio
async def test_kimi_search_uses_followup_tool_message_when_first_call_only_returns_search_id(
    monkeypatch,
):
    captured = []

    class FakeResponse:
        def __init__(self, data):
            self.status = 200
            self._data = data

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def json(self):
            return self._data

        async def text(self):
            return json.dumps(self._data, ensure_ascii=False)

    class FakeSession:
        def __init__(self, responses):
            self._responses = list(responses)

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        def post(self, url, json=None, headers=None):
            captured.append({"url": url, "json": json, "headers": headers})
            return FakeResponse(self._responses.pop(0))

    async def fake_get_key(_provider_settings):
        return "test-kimi-key"

    monkeypatch.setattr(module._KIMI_KEY_ROTATOR, "get", fake_get_key)
    monkeypatch.setattr(
        module.aiohttp,
        "ClientSession",
        lambda trust_env=True: FakeSession(
            [
                {
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": "",
                                "tool_calls": [
                                    {
                                        "id": "call-1",
                                        "type": "builtin_function",
                                        "function": {
                                            "name": "$web_search",
                                            "arguments": json.dumps(
                                                {
                                                    "search_result": {
                                                        "search_id": "abc123",
                                                    }
                                                },
                                                ensure_ascii=False,
                                            ),
                                        },
                                    }
                                ],
                            }
                        }
                    ]
                },
                {
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": "上海今天多云，14℃到24℃，北风3到4级。",
                            }
                        }
                    ]
                },
            ]
        ),
    )

    results = await module._kimi_search(
        {
            "websearch_kimi_api_key": ["test-kimi-key"],
            "websearch_kimi_api_base": "https://api.moonshot.cn/v1",
        },
        {
            "model": "kimi-k2.5",
            "messages": [{"role": "user", "content": "上海市今天天气 2026年4月19日"}],
            "tools": [{"type": "builtin_function", "function": {"name": "$web_search"}}],
            "thinking": {"type": "disabled"},
            "stream": False,
        },
    )

    assert len(captured) == 2
    assert captured[1]["json"]["messages"][1]["tool_calls"][0]["function"]["name"] == "$web_search"
    assert captured[1]["json"]["messages"][2] == {
        "role": "tool",
        "tool_call_id": "call-1",
        "name": "$web_search",
        "content": '{"search_result": {"search_id": "abc123"}}',
    }
    assert results == [
        module.SearchResult(
            title="上海市今天天气 2026年4月19日",
            url="",
            snippet="上海今天多云，14℃到24℃，北风3到4级。",
            favicon=None,
        )
    ]
