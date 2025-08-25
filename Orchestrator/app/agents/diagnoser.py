from typing import Dict, Any, List
from app.core.a2a_models import TaskInput, TaskResult, AgentCard
from app.core.gemini import generate_text


def get_agent_card() -> AgentCard:
    return AgentCard(
        id="diagnoser",
        name="Diagnoser",
        description="Inspects camera logs and identifies likely root causes.",
        capabilities=["diagnose", "classify_issue"],
    )


def _rule_based_parse(logs: str) -> List[Dict[str, Any]]:
    issues: List[Dict[str, Any]] = []
    lowered = logs.lower()
    if "rtsp" in lowered and ("drop" in lowered or "reconnect" in lowered):
        issues.append({
            "component": "stream",
            "finding": "RTSP instability (drops/reconnects)",
            "confidence": 0.7,
            "evidence": "rtsp + drops/reconnect in logs",
        })
    if "timeout" in lowered or "ping" in lowered or "%" in lowered:
        # try to extract packet loss percentage
        import re
        m = re.search(r"(\d+)%", logs)
        loss = int(m.group(1)) if m else None
        issues.append({
            "component": "network",
            "finding": "Intermittent connectivity / packet loss",
            "confidence": 0.75 if loss and loss >= 30 else 0.6,
            "evidence": f"timeout/ping loss{f' {loss}%' if loss is not None else ''}",
            "packet_loss_percent": loss,
        })
    if "firmware" in lowered and ("latest" in lowered or "version" in lowered):
        issues.append({
            "component": "firmware",
            "finding": "Outdated firmware",
            "confidence": 0.8,
            "evidence": "version older than latest",
        })
    return issues


def run(input_data: TaskInput) -> TaskResult:
    issues = _rule_based_parse(input_data.logs)
    system = (
        "You are a diagnostics expert for IP cameras (home/office/street). "
        "Given logs, summarize likely root causes, affected components, and confidence based on the evidence. "
        "Output concise bullet points."
    )
    prompt = f"Logs:\n{input_data.logs}\n\nProvide a brief diagnosis summary."
    text = generate_text(prompt, system)
    details: Dict[str, Any] = {
        "summary": text,
        "issues": issues,
    }
    # Prepare context for downstream agents
    details["context"] = {"diagnosis": {"issues": issues, "summary": text}}
    return TaskResult(status="ok", summary="Diagnosis produced", details=details)
