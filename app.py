"""
Streamlit UI for the BigBuck5 financial agent.
Run: streamlit run app.py
"""

import os

import pandas as pd
import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage

from Config import DATA_FOLDER, STOCKS
from agent import create_agent

# ── Page setup ────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="BigBuck5 | Financial Agent",
    page_icon="📈",
    layout="wide",
)

st.title("BigBuck5 — Investment Decision Support")
st.caption("AI assistant for fund managers · data from local CSV files")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _data_ready() -> bool:
    """True if at least one stock CSV exists under data/."""
    if not os.path.isdir(DATA_FOLDER):
        return False
    return any(
        os.path.exists(os.path.join(DATA_FOLDER, f"{t}.csv")) for t in STOCKS
    )


def _load_chart_df(ticker: str, days: int = 60) -> pd.DataFrame | None:
    """Load recent close prices for the sidebar chart."""
    path = os.path.join(DATA_FOLDER, f"{ticker}.csv")
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    if "close" not in df.columns:
        return None
    subset = df[["close"]].tail(days)
    subset.index = pd.to_datetime(subset.index)
    return subset


def ask_agent(agent, question: str, thread_id: str) -> tuple[str, list[str]]:
    """
    Send one user message through the LangGraph app.
    Returns (final_answer, list of status messages e.g. tool calls).
    """
    config = {"configurable": {"thread_id": thread_id}}
    state = {"messages": [HumanMessage(content=question)]}
    answer = ""
    status_log: list[str] = []

    for event in agent.app.stream(state, config=config):
        for node, payload in event.items():
            if node == "tools":
                status_log.append("Fetched market data from CSV")
            elif node == "BigBuck5":
                msg = payload["messages"][-1]
                if isinstance(msg, AIMessage):
                    if getattr(msg, "tool_calls", None):
                        names = [tc.get("name", "?") for tc in msg.tool_calls]
                        status_log.append(f"Calling tools: {', '.join(names)}")
                    elif msg.content:
                        answer = msg.content
            elif node == "quality_control":
                status_log.append("Quality check ran")

    return answer, status_log


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("Settings")
    model_name = st.text_input("Ollama model", value="gemma4:e2b")
    thread_id = st.text_input("Conversation id", value="streamlit_demo")

    st.divider()
    st.subheader("Market chart")

    available = [
        t for t in STOCKS
        if os.path.exists(os.path.join(DATA_FOLDER, f"{t}.csv"))
    ]
    if not available:
        available = list(STOCKS)

    chart_ticker = st.selectbox("Ticker", available, index=0 if available else None)
    chart_days = st.slider("Days shown", 30, 252, 60)

    if _data_ready() and chart_ticker:
        chart_df = _load_chart_df(chart_ticker, chart_days)
        if chart_df is not None:
            st.line_chart(chart_df, height=220)
            last_close = chart_df["close"].iloc[-1]
            st.metric("Last close", f"${last_close:.2f}")
        else:
            st.warning(f"No chart data for {chart_ticker}")
    else:
        st.error("No CSV data found. Run: python DataLoader.py")

    st.divider()
    st.subheader("Example questions")
    examples = [
        "What is the trading signal for AAPL?",
        "Give me a technical summary of MSFT",
        "Compare AAPL, MSFT and GOOGL",
        "Which stocks are available?",
    ]
    for ex in examples:
        if st.button(ex, key=ex, use_container_width=True):
            st.session_state["pending_question"] = ex


# ── Main chat ─────────────────────────────────────────────────────────────────

if not _data_ready():
    st.warning(
        "Market data missing. From the project folder run:\n\n"
        "```bash\npython DataLoader.py\n```\n\n"
        "Then refresh this page."
    )

if "messages" not in st.session_state:
    st.session_state.messages = []

if "agent" not in st.session_state:
    st.session_state.agent = None
    st.session_state.agent_model = None

# Recreate agent if model name changed
if st.session_state.agent_model != model_name:
    try:
        st.session_state.agent = create_agent(model_name=model_name, use_qc=False)
        st.session_state.agent_model = model_name
    except Exception as e:
        st.session_state.agent = None
        st.error(f"Could not start agent (is Ollama running?): {e}")

# Show chat history
for role, content in st.session_state.messages:
    with st.chat_message(role):
        st.markdown(content)

# Handle example button or chat input
prompt = st.chat_input("Ask about stocks, signals, or comparisons...")
if st.session_state.get("pending_question"):
    prompt = st.session_state.pop("pending_question")

if prompt:
    st.session_state.messages.append(("user", prompt))
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if st.session_state.agent is None:
            reply = "Agent not available. Check Ollama and the model name in the sidebar."
            st.error(reply)
        elif not _data_ready():
            reply = "Cannot answer: no CSV data. Run DataLoader.py first."
            st.warning(reply)
        else:
            with st.spinner("BigBuck5 is thinking..."):
                try:
                    reply, steps = ask_agent(
                        st.session_state.agent, prompt, thread_id
                    )
                    if steps:
                        with st.expander("What happened behind the scenes"):
                            for s in steps:
                                st.write(f"- {s}")
                    if not reply:
                        reply = (
                            "No text answer was generated. "
                            "Try rephrasing or check the Ollama model."
                        )
                except Exception as e:
                    reply = f"Error: {e}"
                    st.exception(e)

        st.markdown(reply)

    st.session_state.messages.append(("assistant", reply))
