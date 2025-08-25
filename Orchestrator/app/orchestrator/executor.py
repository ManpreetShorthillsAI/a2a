from typing import Callable, Dict, Generator, Optional
import httpx
from app.core.a2a_models import Task, TaskResult, Event, TaskInput, AgentCard
from app.agents import diagnoser, fixer, support
from app.orchestrator.registry import AgentRegistry

AgentRun = Callable[[TaskInput], TaskResult]
AgentRegistryEntry = Dict[str, object]


LOCAL_REGISTRY: Dict[str, AgentRegistryEntry] = {
    "diagnoser": {"card": diagnoser.get_agent_card(), "run": diagnoser.run},
    "fixer": {"card": fixer.get_agent_card(), "run": fixer.run},
    "support": {"card": support.get_agent_card(), "run": support.run},
}

REMOTE_REGISTRY = AgentRegistry.from_env_or_file()


def _fetch_remote_card(agent_id: str, base_url: str) -> Optional[AgentCard]:
    try:
        with httpx.Client(timeout=10) as client:
            resp = client.get(f"{base_url}/agent/{agent_id}/card")
            if resp.status_code == 200:
                data = resp.json()
                return AgentCard.model_validate(data)
    except Exception:
        return None
    return None


def _run_remote(agent_id: str, base_url: str, input_data: TaskInput) -> TaskResult:
    try:
        with httpx.Client(timeout=60) as client:
            resp = client.post(
                f"{base_url}/agent/{agent_id}/run",
                json={"logs": input_data.logs, "context": input_data.context},
            )
            if resp.status_code == 200:
                return TaskResult.model_validate(resp.json())
            return TaskResult(status="error", summary=f"Remote {agent_id} HTTP {resp.status_code}", details={})
    except Exception as e:  # noqa: BLE001
        return TaskResult(status="error", summary="Remote agent error", details={"error": str(e)})


def execute(task: Task) -> Generator[Event, None, TaskResult]:
    yield Event(type="task.created", message=f"Task {task.id} created", data=task.model_dump())
    yield Event(type="task.started", message=f"Task {task.id} started", data={"agent": task.agent_id})

    # Resolve remote URL if configured; otherwise use local registry
    remote_url = REMOTE_REGISTRY.get_url(task.agent_id)
    if remote_url:
        card = _fetch_remote_card(task.agent_id, remote_url) or AgentCard(
            id=task.agent_id,
            name=task.agent_id.capitalize(),
            description=f"Remote agent at {remote_url}",
            capabilities=[],
        )
        run = None  # indicates remote
    else:
        entry = LOCAL_REGISTRY.get(task.agent_id)
        if not entry:
            yield Event(type="error", message=f"Unknown agent: {task.agent_id}")
            return TaskResult(status="error", summary="Unknown agent", details={})
        card = entry["card"]
        run: AgentRun = entry["run"]  # type: ignore

    yield Event(
        type="agent.started",
        message=f"{card.name} started",
        data={"agent": card.model_dump(), "agent_id": card.id},
    )

    try:
        if remote_url:
            result = _run_remote(task.agent_id, remote_url, task.input)
            if result.status == "error":
                yield Event(type="error", message=result.summary, data=result.details)
        else:
            result = run(task.input)  # type: ignore[misc]
    except Exception as e:  # noqa: BLE001
        yield Event(type="error", message=str(e))
        return TaskResult(status="error", summary="Agent error", details={"error": str(e)})

    yield Event(
        type="agent.completed",
        message=f"{card.name} completed",
        data={"result": result.model_dump(), "agent_id": card.id},
    )

    # Simple delegation policy: Diagnoser -> Fixer -> Support (conditional)
    if task.agent_id == "diagnoser":
        # Pass the original logs plus diagnosis into Fixer
        # Merge context forward
        next_context = task.input.context or {}
        if result.details.get("context"):
            next_context.update(result.details.get("context"))
        # Provide both original logs and diagnosis summary to Fixer
        diagnosis_summary = result.details.get("summary") or result.details.get("raw", "")
        fixer_input = TaskInput(
            logs=f"Diagnosis + Logs\n\n{diagnosis_summary}\n\n{task.input.logs}",
            context=next_context,
        )
        yield Event(
            type="delegation.requested",
            message="Delegating to Fixer",
            data={"to": "fixer"},
        )
        sub_task = Task(id=f"{task.id}:fix", agent_id="fixer", input=fixer_input)
        sub_result = yield from execute(sub_task)
        yield Event(
            type="delegation.completed",
            message="Fixer finished",
            data=sub_result.model_dump(),
        )
        if sub_result.status == "needs_support":
            # Merge context
            support_context = fixer_input.context or {}
            if sub_result.details.get("context"):
                support_context.update(sub_result.details.get("context"))
            support_input = TaskInput(
                logs=f"Need support. Context:\n\n{sub_result.details.get('plan', '')}\n\n{task.input.logs}",
                context=support_context,
            )
            yield Event(
                type="delegation.requested",
                message="Delegating to Support",
                data={"to": "support"},
            )
            support_task = Task(id=f"{task.id}:support", agent_id="support", input=support_input)
            support_result = yield from execute(support_task)
            yield Event(
                type="delegation.completed",
                message="Support finished",
                data=support_result.model_dump(),
            )
            yield Event(type="task.completed", message="Task fully completed")
            return support_result
        else:
            yield Event(type="task.completed", message="Task completed with Fixer result")
            return sub_result

    # If not diagnoser entry point, we just return the agent result
    yield Event(type="task.completed", message="Task completed")
    return result
