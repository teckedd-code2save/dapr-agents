# Agent performance tests (work in progress)

The deterministic fixture isolates provider latency from agent execution. Start it from the repository root:

```sh
PERF_LLM_LATENCY_MS=20 PERF_LLM_TOOL_CALLS=3 uv run uvicorn --app-dir tests/perf/common mock_llm:app --host 127.0.0.1 --port 8089
uv run pytest tests/perf/common/test_mock_llm.py
```

The OpenAI-compatible base URL is http://127.0.0.1:8089/v1. Tool calls target a benchmark tool accepting an integer `value`. The fixture supports non-streaming chat completions only. Token counts are synthetic and must not be used for token throughput measurements.

This initial fixture is not yet an end-to-end benchmark or a published baseline.

## Local agent and k6

Initialize Dapr with its local Redis and scheduler. With the mock running in another terminal:

```sh
OPENAI_API_KEY=perf OPENAI_BASE_URL=http://127.0.0.1:8089/v1 PERF_ENABLE_TOOLS=1 dapr run --app-id perf-agent --app-port 8001 --resources-path quickstarts/resources -- uv run python tests/perf/common/agent_app.py
```

Run the scenario-specific k6 command from the repository root. For HTTP-only tests set both tool counts and enablement to zero. Stop the agent and mock between configurations. Use isolated infrastructure; do not run against production.

## Outstanding before upstream PR

- Execute fixture tests and required repository checks; verify native workflow completion and actual tool fan-out.
- Add resource and state-growth collection, summary tables/charts, Kubernetes k6-operator setup, and manual CI workflow.
- Run and publish a versioned current-release baseline; distinguish mock and optional Ollama results.
- Verify DCO sign-off and review all changes before opening a PR.
