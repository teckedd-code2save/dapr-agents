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

"""Contract tests for the deterministic performance fixture."""

from pathlib import Path
import runpy

import pytest
from fastapi.testclient import TestClient

create_app = runpy.run_path(str(Path(__file__).with_name("mock_llm.py")))["create_app"]


def test_completion() -> None:
    client = TestClient(create_app())
    response = client.post(
        "/v1/chat/completions",
        json={"model": "perf", "messages": [{"role": "user", "content": "test"}]},
    )
    assert response.status_code == 200
    assert response.json()["choices"][0]["finish_reason"] == "stop"


def test_tool_round_trip() -> None:
    client = TestClient(create_app(tool_calls=3))
    body = {
        "model": "perf",
        "messages": [{"role": "user", "content": "test"}],
        "tools": [{"type": "function", "function": {"name": "echo"}}],
    }
    choice = client.post("/v1/chat/completions", json=body).json()["choices"][0]
    calls = choice["message"]["tool_calls"]
    assert choice["finish_reason"] == "tool_calls"
    assert len({call["id"] for call in calls}) == 3
    body["messages"].append(choice["message"])
    body["messages"].extend(
        {"role": "tool", "tool_call_id": call["id"], "content": "ok"}
        for call in calls
    )
    assert (
        client.post("/v1/chat/completions", json=body).json()["choices"][0][
            "finish_reason"
        ]
        == "stop"
    )


def test_negative_configuration() -> None:
    with pytest.raises(ValueError):
        create_app(latency_ms=-1)
