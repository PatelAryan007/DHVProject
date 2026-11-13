"""
NIRF Insight — Sidebar Component
Renders branding and footer in the sidebar.
"""

import streamlit as st


def render_sidebar_branding():
    """Display the NIRF Insight logo and tagline in the sidebar."""
    st.sidebar.markdown(
        """
        <div class="sidebar-brand">
            <div class="sidebar-brand-inner">
                <div class="sidebar-brand-icon">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M3 3v18h18" />
                        <path d="M18 17V9" />
                        <path d="M13 17V5" />
                        <path d="M8 17v-3" />
                    </svg>
                </div>
                <div class="sidebar-brand-text">
                    <div class="sidebar-logo">NIRF Insight</div>
                    <div class="sidebar-tagline">Higher Education Analytics</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_footer():
    """Display version and dataset info at the bottom of the sidebar."""
    st.sidebar.markdown(
        """
        <div class="sidebar-footer">
            <hr class="sidebar-footer-divider">
            <div class="sidebar-footer-content">
                <strong>NIRF Insight</strong> &nbsp;·&nbsp; v1.0<br>
                <span>Dataset: 2017 – 2025</span><br>
                <span class="footer-course">DHV Course Project</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
