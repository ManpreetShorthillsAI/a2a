from typing import Dict, Any
from app.core.a2a_models import TaskInput, TaskResult, AgentCard


_FAKE_DB: Dict[str, Dict[str, Any]] = {}


def get_agent_card() -> AgentCard:
    return AgentCard(
        id="support",
        name="Support",
        description="Creates a mock support ticket and returns the ticket id.",
        capabilities=["ticket_create"],
    )


def run(input_data: TaskInput) -> TaskResult:
    import uuid

    ticket_id = str(uuid.uuid4())[:8]
    diagnosis = (input_data.context or {}).get("diagnosis", {})
    fix_plan = (input_data.context or {}).get("fix_plan", {})
    severity = "medium"
    if "packet_loss_percent" in str(diagnosis):
        try:
            loss_vals = [i.get("packet_loss_percent") for i in diagnosis.get("issues", []) if i.get("packet_loss_percent")]
            if any(v and v >= 30 for v in loss_vals):
                severity = "high"
        except Exception:
            pass
    payload = {
        "title": "Camera issue reported",
        "body": input_data.logs[:1000],
        "status": "open",
        "severity": severity,
        "context": {
            "diagnosis": diagnosis,
            "fix_plan": fix_plan,
        },
    }
    _FAKE_DB[ticket_id] = payload
    return TaskResult(
        status="ok",
        summary=f"Support ticket created: {ticket_id}",
        details={"ticket_id": ticket_id, "payload": payload},
    )
