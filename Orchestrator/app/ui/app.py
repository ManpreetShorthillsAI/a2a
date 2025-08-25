import os
import sys
from pathlib import Path

# Ensure project root is on sys.path so "app" resolves to the package, not this script
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st
from app.core.a2a_models import Task, TaskInput
from app.orchestrator.executor import execute

st.set_page_config(page_title="Camera Agent Orchestrator (A2A POC)", layout="wide")

st.title("Camera Agent Orchestrator (A2A POC)")
st.caption("Agents: Diagnoser → Fixer → Support. Powered by Gemini. POC, mocked where needed.")

if not os.getenv("GEMINI_API_KEY"):
    st.warning("GEMINI_API_KEY is not set. Set it in your environment before running tasks.")

with st.sidebar:
    st.header("Run Settings")
    entry_agent = st.selectbox("Entry Agent", options=["diagnoser", "fixer", "support"], index=0)
    task_id = st.text_input("Task ID", value="task-1")
    st.caption("If agents.local.json is present, agents will be called remotely over HTTP.")

sample_logs = (
    "[2025-01-02 10:01:22] camera-1: RTSP stream drops every 30s; reconnect attempt failed.\n"
    "[2025-01-02 10:01:25] camera-1: Network timeout to 192.168.1.10; ping loss 40%.\n"
    "[2025-01-02 10:02:12] camera-1: Firmware check: version v1.2.3 (latest v1.5.0).\n"
)

logs = st.text_area("Paste camera logs", value=sample_logs, height=220)
with st.expander("Advanced context (optional)"):
    ctx_diag = st.checkbox("Assume diagnosis context from previous run", value=True)
    context = {}
    if ctx_diag:
        # In a real app this might be persisted; here we show the shape
        context = {"diagnosis": {"issues": [], "summary": ""}}
run = st.button("Run")

placeholder = st.empty()
col_diag, col_fix, col_support = st.columns(3)
with col_diag:
    diag_box = st.container(border=True)
with col_fix:
    fix_box = st.container(border=True)
with col_support:
    support_box = st.container(border=True)

if run:
    task = Task(id=task_id, agent_id=entry_agent, input=TaskInput(logs=logs, context=context))
    with st.status("Running...", expanded=True) as status:
        st.write("Task created and started")
        gen = execute(task)
        result = None
        try:
            while True:
                event = next(gen)
                with placeholder.container():
                    st.write(f"[{event.type}] {event.message}")
                    if event.data:
                        st.code(str(event.data))
                # Show intermediate per-agent results
                if event.type == "agent.completed" and event.data:
                    agent_id = event.data.get("agent_id")
                    result = event.data.get("result")
                    if agent_id == "diagnoser" and result:
                        with diag_box:
                            st.subheader("Diagnoser Result")
                            st.json(result)
                    elif agent_id == "fixer" and result:
                        with fix_box:
                            st.subheader("Fixer Result")
                            st.json(result)
                    elif agent_id == "support" and result:
                        with support_box:
                            st.subheader("Support Ticket")
                            st.json(result)
        except StopIteration as stop:
            result = stop.value
        status.update(label="Done", state="complete")

    st.subheader("Final Result")
    if result is not None:
        st.success(result.summary)
        with st.expander("Structured result", expanded=True):
            st.json(result.model_dump())
