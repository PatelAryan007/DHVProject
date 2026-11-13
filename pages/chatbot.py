"""
NIRF Insight — AI Chatbot Interface
====================================
Natural language conversational interface powered by OpenAI API integration
and grounded Python/Pandas analytics over the 2017–2025 NIRF dataset.
"""

import streamlit as st
import pandas as pd

from core.data_loader import load_data
from components.header import render_page_header
from components.charts import render_chart
from chatbot.llm_service import is_openai_configured, get_configured_model
from chatbot.conversation_manager import ConversationManager
from chatbot.chatbot_service import process_user_message

# ---------------------------------------------------------------------------
# Page Setup & Header
# ---------------------------------------------------------------------------

render_page_header(
    "NIRF Insight AI Assistant",
    "Ask analytical questions about the NIRF higher education rankings in plain English. "
    "Answers, statistical insights, data tables, and interactive charts are generated live.",
)

df = load_data()
if df is None:
    st.error("⚠️ Dataset not found. Place `nirf_2017_2025_clean.csv` in `data/`.")
    st.stop()

# Initialize Session State
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

conv_manager = ConversationManager(st.session_state.chat_messages)

# ---------------------------------------------------------------------------
# API Status Badge & Configuration Helper
# ---------------------------------------------------------------------------

openai_active = is_openai_configured()
model_name = get_configured_model()

if openai_active:
    st.markdown(
        f"""
        <div style="background:#EBF2ED; border:1px solid #C4D7C9; border-radius:8px; padding:0.5rem 0.9rem; margin-bottom:1rem; display:flex; justify-content:space-between; align-items:center;">
            <div style="font-size:0.85rem; color:#27352C;">
                🟢 <strong>OpenAI Engine Connected:</strong> Model <code>{model_name}</code> is active.
            </div>
            <span style="font-size:0.75rem; background:#3D6247; color:#FFFFFF; padding:0.2rem 0.6rem; border-radius:10px;">Live AI Mode</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    with st.expander("ℹ️ OpenAI API Key Status (Optional Setup)", expanded=False):
        st.markdown(
            """
            **OpenAI Engine is currently running in Grounded Heuristic Analytics Mode.**
            
            You can ask all natural-language questions immediately! Calculations, data tables, and charts are calculated live using Pandas.
            
            **To connect your official OpenAI API Key for deep conversational NLU:**
            1. Copy `.env.example` to `.env` in the project root:
               ```bash
               cp .env.example .env
               ```
            2. Add your key inside `.env`:
               ```env
               OPENAI_API_KEY=sk-proj-your-actual-key-here
               OPENAI_MODEL=gpt-4o-mini
               ```
            3. Restart the Streamlit dashboard.
            """
        )

# ---------------------------------------------------------------------------
# Suggested Prompts (Visible when conversation is empty)
# ---------------------------------------------------------------------------

SUGGESTED_PROMPTS = [
    "🏆 Top 10 Engineering institutions in 2025",
    "📈 Average NIRF score trend over time",
    "🔬 Compare IIT Madras and IIT Bombay",
    "📍 Which state has the most top institutions?",
    "🔗 Correlation between RPC and overall Score",
]

if not st.session_state.chat_messages:
    st.markdown("**💡 Suggested Questions to Get Started:**")
    p_cols = st.columns(len(SUGGESTED_PROMPTS))
    for idx, prompt in enumerate(SUGGESTED_PROMPTS):
        with p_cols[idx]:
            clean_p = prompt.split(" ", 1)[1] if " " in prompt else prompt
            if st.button(prompt, key=f"sug_btn_{idx}", use_container_width=True):
                # Trigger processing
                with st.spinner("Analyzing NIRF dataset…"):
                    process_user_message(clean_p, df, conv_manager)
                    st.rerun()

    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Render Conversation Turns
# ---------------------------------------------------------------------------

for turn_idx, msg in enumerate(st.session_state.chat_messages):
    role = msg.get("role", "assistant")
    content = msg.get("content", "")

    with st.chat_message(role):
        st.markdown(content)

        # If turn includes a generated Plotly figure
        fig = msg.get("fig")
        if fig is not None:
            render_chart(fig, key=f"chat_chart_{turn_idx}")

        # If turn includes supporting tabular data
        table = msg.get("table")
        if isinstance(table, pd.DataFrame) and not table.empty:
            with st.expander(f"📋 Supporting Data Table ({len(table)} records)", expanded=False):
                st.dataframe(table, use_container_width=True, hide_index=True)
                csv_bytes = table.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="⬇️ Download Data as CSV",
                    data=csv_bytes,
                    file_name=f"nirf_chat_result_{turn_idx}.csv",
                    mime="text/csv",
                    key=f"dl_chat_csv_{turn_idx}",
                )

# ---------------------------------------------------------------------------
# Chat Input & Streamlit Processing Loop
# ---------------------------------------------------------------------------

user_input = st.chat_input("Ask any question about NIRF rankings, scores, or institutions…")

if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing NIRF dataset…"):
            response = process_user_message(user_input, df, conv_manager)

            st.markdown(response.answer_text)

            if response.fig is not None:
                render_chart(response.fig, key=f"chat_live_chart_{len(st.session_state.chat_messages)}")

            if isinstance(response.table, pd.DataFrame) and not response.table.empty:
                with st.expander(f"📋 Supporting Data Table ({len(response.table)} records)", expanded=True):
                    st.dataframe(response.table, use_container_width=True, hide_index=True)
                    csv_bytes = response.table.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        label="⬇️ Download Data as CSV",
                        data=csv_bytes,
                        file_name="nirf_chat_result.csv",
                        mime="text/csv",
                        key="dl_live_chat_csv",
                    )

    st.rerun()

# ---------------------------------------------------------------------------
# Clear Chat Action Button
# ---------------------------------------------------------------------------

if st.session_state.chat_messages:
    st.markdown("")
    col_clear, _ = st.columns([1, 4])
    with col_clear:
        if st.button("🗑️ Clear Conversation", key="clear_chat_history", use_container_width=True):
            conv_manager.clear()
            st.session_state.chat_messages = []
            st.rerun()
