"""
NIRF Insight — KPI Cards Component
Renders attractive metric/KPI cards in a responsive row.
"""

import streamlit as st


def render_kpi_cards(metrics: list[dict]):
    """Render a row of KPI cards.

    Each dict in *metrics* should contain:
        - ``label`` — short title
        - ``value`` — displayed number/text
        - ``icon``  — emoji icon
    """
    if not metrics:
        return

    cols = st.columns(len(metrics))
    for col, m in zip(cols, metrics):
        with col:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-icon">{m.get('icon', '📊')}</div>
                    <div class="kpi-value">{m.get('value', '—')}</div>
                    <div class="kpi-label">{m.get('label', '')}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_single_kpi(label: str, value, icon: str = "📊"):
    """Render one standalone KPI card."""
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-icon">{icon}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-label">{label}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
