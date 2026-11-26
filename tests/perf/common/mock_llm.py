#
# Copyright 2026 The Dapr Authors
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""Deterministic OpenAI-compatible fixture for agent performance tests."""

import asyncio
import json
import os
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field


class CompletionRequest(BaseModel):
    model: str
    messages: list[dict[str, Any]]
    tools: list[dict[str, Any]] = Field(default_factory=list)
    stream: bool = False


def create_app(latency_ms: int = 0, tool_calls: int = 0) -> FastAPI:
    if latency_ms < 0 or tool_calls < 0:
        raise ValueError("Latency and tool count must be nonnegative")

    app = FastAPI()

    @app.get("/healthz")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/v1/chat/completions")
    async def complete(request: CompletionRequest) -> dict[str, Any]:
        from fastapi import HTTPException

        if request.stream:
            raise HTTPException(400, "Streaming is not supported by this fixture")
        await asyncio.sleep(latency_ms / 1000)
        message: dict[str, Any] = {"role": "assistant", "content": "Benchmark complete"}
        reason = "stop"
        # Only inspect the current turn, not tool results from earlier turns.
        last_user = max(
            (i for i, m in enumerate(request.messages) if m.get("role") == "user"),
            default=-1,
        )
        if tool_calls and request.tools and not any(
            m.get("role") == "tool" for m in request.messages[last_user + 1 :]
        ):
            name = request.tools[0]["function"]["name"]
            message["content"] = None
            message["tool_calls"] = [
                {
                    "id": f"call_perf_{i}",
                    "type": "function",
                    "function": {
                        "name": name,
                        "arguments": json.dumps({"value": i}),
                    },
                }
                for i in range(tool_calls)
            ]
            reason = "tool_calls"
        return {
            "id": "chatcmpl-perf",
            "object": "chat.completion",
            "created": 0,
            "model": request.model,
            "choices": [{"index": 0, "message": message, "finish_reason": reason}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        }

    return app


app = create_app(
    latency_ms=int(os.getenv("PERF_LLM_LATENCY_MS", "0")),
    tool_calls=int(os.getenv("PERF_LLM_TOOL_CALLS", "0")),
)
