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

"""Run a real DurableAgent against the benchmark LLM fixture."""

import os

from dapr_agents import AgentRunner, DurableAgent, tool
from dapr_agents.agents.configs import AgentMemoryConfig, AgentStateConfig
from dapr_agents.llm import OpenAIChatClient
from dapr_agents.memory import ConversationDaprStateMemory
from dapr_agents.storage.daprstores.stateservice import StateStoreService


@tool
def echo(value: int) -> str:
    """Return the supplied integer as text."""
    return str(value)


def main() -> None:
    agent = DurableAgent(
        name="PerfAgent",
        role="Benchmark assistant",
        instructions=["Complete the benchmark task."],
        llm=OpenAIChatClient(model=os.getenv("PERF_MODEL", "perf")),
        tools=[echo] if os.getenv("PERF_ENABLE_TOOLS") == "1" else [],
        memory=AgentMemoryConfig(
            store=ConversationDaprStateMemory(store_name="agent-memory")
        ),
        state=AgentStateConfig(
            store=StateStoreService(store_name="agent-workflow")
        ),
    )
    runner = AgentRunner()
    try:
        runner.serve(agent, host="0.0.0.0", port=8001)
    finally:
        runner.shutdown()


if __name__ == "__main__":
    main()
