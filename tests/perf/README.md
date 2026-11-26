# Agent performance tests (work in progress)

The deterministic fixture isolates provider latency from agent execution. Start it from the repository root:

```sh
PERF_LLM_LATENCY_MS=20 PERF_LLM_TOOL_CALLS=3 uv run uvicorn --app-dir tests/perf/common mock_llm:app --host 127.0.0.1 --port 8089
uv run pytest tests/perf/common/test_mock_llm.py
```

The OpenAI-compatible base URL is http://127.0.0.1:8089/v1. Tool calls target a benchmark tool accepting an integer `value`. The fixture supports non-streaming chat completions only. Token counts are synthetic and must not be used for token throughput measurements.

This initial fixture is not yet an end-to-end benchmark or a published baseline.
