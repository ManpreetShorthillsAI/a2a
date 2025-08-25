from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any, Optional
from app.core.a2a_models import TaskInput, TaskResult, AgentCard
from app.agents import diagnoser, fixer, support

app = FastAPI(title="Agent Server")

AGENTS = {
    "diagnoser": diagnoser,
    "fixer": fixer,
    "support": support,
}


class RunRequest(BaseModel):
    logs: str
    context: Optional[Dict[str, Any]] = None


@app.get("/agent/{agent_id}/card", response_model=AgentCard)
def get_card(agent_id: str):
    if agent_id not in AGENTS:
        return AgentCard(id=agent_id, name=agent_id, description="Unknown agent", capabilities=[])
    return AGENTS[agent_id].get_agent_card()


@app.post("/agent/{agent_id}/run", response_model=TaskResult)
def run(agent_id: str, req: RunRequest):
    if agent_id not in AGENTS:
        return TaskResult(status="error", summary="Unknown agent", details={})
    module = AGENTS[agent_id]
    return module.run(TaskInput(logs=req.logs, context=req.context))

# To run locally on a machine dedicating a specific agent, use:
# uvicorn app.server.agent_server:app --host 0.0.0.0 --port 9001
