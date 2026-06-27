import streamlit as st
from agent import AgentDesk

st.set_page_config(page_title="AgentDesk", layout="wide")
st.title("🤖 AgentDesk — Tool-Calling AI Agent")
st.caption("Built with the Anthropic API. Demonstrates the core agentic loop: calculator, web search, and file reader tools.")

if "agent" not in st.session_state:
    st.session_state.agent = AgentDesk()
if "history" not in st.session_state:
    st.session_state.history = []

agent = st.session_state.agent

if agent.demo_mode:
    st.info("⚠️ Running in DEMO MODE — no ANTHROPIC_API_KEY detected. Set it in your .env to enable live Claude responses.")
else:
    st.success("✅ Connected to Claude — live tool-calling enabled.")

for role, msg in st.session_state.history:
    with st.chat_message(role):
        st.markdown(msg)

user_input = st.chat_input("Ask AgentDesk something...")

if user_input:
    st.session_state.history.append(("user", user_input))
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            answer = agent.run(user_input, verbose=False)
        st.markdown(answer)

    st.session_state.history.append(("assistant", answer))