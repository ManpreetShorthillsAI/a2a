# Orchestrator A2A POC (Diagnoser, Fixer, Support)

This is a proof-of-concept that mimics an Agent2Agent (A2A) style workflow with three agents powered by Gemini:

- Diagnoser: inspects camera system logs and identifies likely issues
- Fixer: proposes actionable steps or mock fixes for identified issues
- Support: raises a mock support ticket if human intervention is needed

A minimal Streamlit UI lets you paste logs, select agent(s), and stream the run.

References: See the A2A protocol overview at [`https://a2a-protocol.org/latest/`](https://a2a-protocol.org/latest/).

## Setup

```bash
cd /Users/shtlpmac090/Desktop/Orchestrator

# Option 1: Use local virtual environment
python3 -m venv .venv
. .venv/bin/activate

# Option 2: Use centralized environment (recommended)
source /Users/shtlpmac090/Desktop/environments/orchestrator-env/bin/activate

python -m pip install --upgrade pip
pip install -e .
cp .env.example .env  # then edit GEMINI_API_KEY in .env
```

## Run UI

```bash
# Activate the environment
source /Users/shtlpmac090/Desktop/environments/orchestrator-env/bin/activate

# Or if using local environment:
# . .venv/bin/activate

streamlit run app/ui/app.py
```

## Multi-host (separate machines per agent)

You can deploy each agent on its own machine with a small FastAPI server and have the orchestrator call them over HTTP.

1) On each machine, run the agent server with only that agent enabled (use the same repo or copy the agent code):

```bash
# Activate the environment
source /Users/shtlpmac090/Desktop/environments/orchestrator-env/bin/activate

# Or if using local environment:
# . .venv/bin/activate

uvicorn app.server.agent_server:app --host 0.0.0.0 --port 9001  # diagnoser host
# uvicorn app.server.agent_server:app --host 0.0.0.0 --port 9002  # fixer host
# uvicorn app.server.agent_server:app --host 0.0.0.0 --port 9003  # support host
```

2) On the orchestrator machine, create `agents.local.json` mapping agent IDs to base URLs (a sample file is provided):

```json
{
  "diagnoser": "http://diagnoser-host:9001",
  "fixer": "http://fixer-host:9002",
  "support": "http://support-host:9003"
}
```

Alternatively, point to a custom path via `A2A_AGENT_REGISTRY=/path/to/agents.json`.

3) Run the Streamlit UI on the orchestrator machine as usual. The executor will route to remote agents when a URL is configured; otherwise it will use the local in-process agents.

Endpoints (A2A-inspired):
- GET `/agent/{agent_id}/card` → agent capabilities metadata
- POST `/agent/{agent_id}/run` with `{ "logs": "..." }` → returns `TaskResult`

## Notes
- This POC uses Gemini via `google-generativeai`.
- The A2A spec informs shapes like AgentCard, Task, and Events, but this is a simplified, self-contained demo. Learn more at the official site: [`https://a2a-protocol.org/latest/`](https://a2a-protocol.org/latest/).
