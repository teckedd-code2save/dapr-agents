# DurableAgent tool calls performance

## Glossary

- VU: concurrent virtual user.
- Completion: elapsed time from HTTP start to successful terminal workflow status.
- Throughput: successful completed runs per second.

## Test plan

Run the mock LLM and agent as described in [the suite README](../README.md), with PERF_LLM_TOOL_CALLS=3 and PERF_ENABLE_TOOLS=1 respectively. Use a fresh isolated state store for each measured run.

```sh
SCENARIO=t_1_5 SUMMARY_PATH=summary.json k6 run tests/perf/durable-agent-tools/test.js
```

Scale to t_10_100 and t_30_300 after the smoke test passes. Record request latency, completion latency, successful throughput and failure/timeout rates. Verify actual tool execution in agent traces before accepting fan-out results.
