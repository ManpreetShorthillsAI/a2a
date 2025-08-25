import json
import os
from typing import Dict, Optional

_DEFAULT_REGISTRY = {
    # Fallback: no remote; use local functions
}


class AgentRegistry:
    def __init__(self, mapping: Dict[str, str]):
        self.mapping = mapping

    @classmethod
    def from_env_or_file(cls) -> "AgentRegistry":
        path = os.getenv("A2A_AGENT_REGISTRY") or os.path.join(os.getcwd(), "agents.local.json")
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return cls(mapping={k: str(v) for k, v in data.items()})
            except Exception:
                pass
        return cls(mapping=_DEFAULT_REGISTRY)

    def get_url(self, agent_id: str) -> Optional[str]:
        return self.mapping.get(agent_id)
