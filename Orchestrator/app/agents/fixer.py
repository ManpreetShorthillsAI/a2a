from typing import Dict, Any, List
from app.core.a2a_models import TaskInput, TaskResult, AgentCard
from app.core.gemini import generate_text


def get_agent_card() -> AgentCard:
    return AgentCard(
        id="fixer",
        name="Fixer",
        description="Proposes steps or mock fixes for camera issues.",
        capabilities=["fix", "remediation"],
    )


def _baseline_plan(issues: List[Dict[str, Any]]) -> List[str]:
    steps: List[str] = []
    comps = {i.get("component") for i in issues}
    if "network" in comps:
        steps += [
            "Check Ethernet/Wi‑Fi stability; reseat cables or change AP channel.",
            "Run ping for 5 minutes to gateway and NVR; ensure <1% loss.",
            "If on PoE, verify power budget and switch logs for errors.",
        ]
    if "stream" in comps:
        steps += [
            "Lower RTSP bitrate/resolution temporarily to stabilize.",
            "Verify RTSP URL auth/transport; prefer TCP over UDP in unstable nets.",
        ]
    if "firmware" in comps:
        steps += [
            "Backup config and upgrade firmware to the latest stable version.",
            "Factory reset if upgrade fails; restore config and retest.",
        ]
    if not steps:
        steps = [
            "Power‑cycle camera and networking gear.",
            "Check NVR/recording server health and storage errors.",
        ]
    return steps


def run(input_data: TaskInput) -> TaskResult:
    issues = input_data.context.get("diagnosis", {}).get("issues") if input_data.context else None
    issues = issues or []
    base_steps = _baseline_plan(issues)
    system = (
        "You are a remediation expert for IP cameras. Combine the baseline steps with additional safe, "
        "practical steps tailored to the provided diagnosis. Return a short numbered list."
    )
    prompt = (
        "Diagnosis context (JSON-like):\n"
        f"{issues}\n\n"
        f"Logs:\n{input_data.logs}\n\n"
        "Propose a fix plan in steps (1-7)."
    )
    llm_steps_text = generate_text(prompt, system)
    details: Dict[str, Any] = {"plan": llm_steps_text, "baseline": base_steps}
    # Simple escalation heuristic
    lowered = f"{llm_steps_text} {' '.join(base_steps)}".lower()
    status = "needs_support" if any(k in lowered for k in ["rma", "support", "ticket", "hardware fault"]) else "ok"
    # Propagate context forward
    ctx = input_data.context or {}
    ctx["fix_plan"] = {"baseline": base_steps, "llm": llm_steps_text}
    details["context"] = ctx
    return TaskResult(status=status, summary="Fix plan produced", details=details)
