"""
Material Design 3 Light Theme (Google Style) for Streamlit.
This module injects custom CSS to override Streamlit's default dark theme.
"""

import streamlit as st

MATERIAL3_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');

:root {
    /* M3 Light Theme Tokens (Google Style) */
    --md-primary: #1a73e8;
    --md-on-primary: #ffffff;
    --md-primary-container: #d3e3fd;
    --md-on-primary-container: #041e49;
    
    --md-surface: #ffffff;
    --md-on-surface: #1f1f1f;
    --md-surface-variant: #f1f3f4;
    --md-on-surface-variant: #444746;
    
    --md-error: #d93025;
    --md-on-error: #ffffff;
    --md-error-container: #fce8e6;
    --md-on-error-container: #601410;
    
    /* Workspace specific success */
    --md-success: #188038;
    --md-success-container: #e6f4ea;
    
    /* Warning / Alert */
    --md-warning: #b06000;
    --md-warning-container: #fef7e0;
    --md-on-warning-container: #7a5900;
    
    --md-outline: #dadce0;
    --md-background: #ffffff;
    --md-on-background: #1f1f1f;
    
    /* Elevation / Shadows */
    --md-elevation-1: 0 1px 2px 0 rgba(60,64,67,0.3), 0 1px 3px 1px rgba(60,64,67,0.15);
    --md-elevation-2: 0 1px 2px 0 rgba(60,64,67,0.3), 0 2px 6px 2px rgba(60,64,67,0.15);
    
    /* Shapes */
    --md-shape-card: 12px;
    --md-shape-button: 100px; /* Pill */
    --md-shape-chip: 8px;
    
    /* Typography */
    --md-font-family: 'Roboto', 'Google Sans', sans-serif;
}

/* 1. Global Typography & Background */
.stApp {
    font-family: var(--md-font-family) !important;
    background-color: var(--md-background) !important;
    color: var(--md-on-background) !important;
}

[data-testid="stSidebar"] {
    background-color: var(--md-surface-variant) !important;
    border-right: 1px solid var(--md-outline) !important;
}

/* Base Headings */
h1, h2, h3, h4, h5, h6 {
    font-family: var(--md-font-family) !important;
    font-weight: 500 !important;
    color: var(--md-on-background) !important;
}

/* Base text */
p, span, div, label {
    color: var(--md-on-background);
}

/* 2 & 3. Target Component: Alert Box & Status Cards */
/* By default make all warnings M3 style (if we can't detect by color) */
.stAlert, div[data-testid="stAlert"] {
    border-radius: var(--md-shape-chip) !important;
    border: none !important;
    box-shadow: var(--md-elevation-1) !important;
    background-color: var(--md-surface) !important;
}

/* Error (Red) - checking for typical Streamlit SVG color or st-ae class */
div[data-testid="stAlert"]:has(svg:first-child) {
    border-radius: var(--md-shape-chip) !important;
    padding: 12px 16px !important;
    border-left: 4px solid transparent !important;
}

/* We use CSS nesting trick to target specific alert colors from Streamlit's injected SVG colors or internal classes */
/* Error override */
div[data-testid="stAlert"]:has(svg[color="red"]), div[data-testid="stAlert"]:has(svg[color="#ff2b2b"]) {
    background-color: var(--md-error-container) !important;
    border-left-color: var(--md-error) !important;
}
div[data-testid="stAlert"]:has(svg[color="red"]) .stMarkdown p, div[data-testid="stAlert"]:has(svg[color="#ff2b2b"]) .stMarkdown p {
    color: var(--md-error) !important;
}

/* Success override */
div[data-testid="stAlert"]:has(svg[color="green"]), div[data-testid="stAlert"]:has(svg[color="#09ab3b"]) {
    background-color: var(--md-success-container) !important;
    border-left-color: var(--md-success) !important;
}
div[data-testid="stAlert"]:has(svg[color="green"]) .stMarkdown p, div[data-testid="stAlert"]:has(svg[color="#09ab3b"]) .stMarkdown p {
    color: var(--md-success) !important;
}

/* Info override */
div[data-testid="stAlert"]:has(svg[color="blue"]), div[data-testid="stAlert"]:has(svg[color="#0068c9"]) {
    background-color: var(--md-primary-container) !important;
    border-left-color: var(--md-primary) !important;
}
div[data-testid="stAlert"]:has(svg[color="blue"]) .stMarkdown p, div[data-testid="stAlert"]:has(svg[color="#0068c9"]) .stMarkdown p {
    color: var(--md-primary) !important;
}

/* Warning override (Gemini warning) */
div[data-testid="stAlert"]:has(svg[color="orange"]), div[data-testid="stAlert"]:has(svg[color="#ff9900"]), div[data-testid="stAlert"]:has(svg[color="#ffc107"]) {
    background-color: var(--md-warning-container) !important;
    border-left-color: var(--md-warning) !important;
}
div[data-testid="stAlert"]:has(svg[color="orange"]) .stMarkdown p, div[data-testid="stAlert"]:has(svg[color="#ff9900"]) .stMarkdown p {
    color: var(--md-on-warning-container) !important;
}


/* 4. Buttons (Filled Primary / Outlined Secondary) */
.stButton > button {
    border-radius: var(--md-shape-button) !important;
    font-family: var(--md-font-family) !important;
    font-weight: 500 !important;
    padding: 10px 24px !important;
    transition: all 0.2s cubic-bezier(0.2, 0, 0, 1) !important;
    text-transform: none !important;
}

/* Primary Button (Filled) */
.stButton > button[kind="primary"] {
    background-color: var(--md-primary) !important;
    color: var(--md-on-primary) !important;
    border: none !important;
    box-shadow: var(--md-elevation-1) !important;
}
.stButton > button[kind="primary"]:hover {
    box-shadow: var(--md-elevation-2) !important;
    transform: translateY(-1px) !important;
    background-color: #1557b0 !important; /* Slightly darker */
}
.stButton > button[kind="primary"]:active {
    box-shadow: var(--md-elevation-1) !important;
    transform: scale(0.98) !important;
}

/* Secondary Button (Outlined) */
.stButton > button[kind="secondary"] {
    background-color: transparent !important;
    color: var(--md-primary) !important;
    border: 1px solid var(--md-outline) !important;
}
.stButton > button[kind="secondary"]:hover {
    background-color: rgba(26, 115, 232, 0.04) !important;
    border-color: var(--md-primary) !important;
}
.stButton > button[kind="secondary"]:active {
    background-color: rgba(26, 115, 232, 0.1) !important;
    transform: scale(0.98) !important;
}

/* 5. Progress Bar */
div[data-testid="stProgress"] {
    background-color: var(--md-surface-variant) !important;
    border-radius: var(--md-shape-button) !important;
    overflow: hidden;
    height: 8px !important;
}
div[data-testid="stProgress"] > div > div {
    background-color: var(--md-primary) !important;
    border-radius: var(--md-shape-button) !important;
}

/* 6. Avatar Circle */
.gauth-avatar-wrap {
    display: inline-flex;
    align-items: center;
    gap: 12px;
    padding: 8px 12px;
    border-radius: var(--md-shape-button) !important;
    background-color: var(--md-surface) !important;
    border: 1px solid var(--md-outline) !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
    transition: all 0.2s;
}
.gauth-avatar-wrap:hover {
    box-shadow: var(--md-elevation-1) !important;
    background-color: var(--md-surface-variant) !important;
}
.gauth-avatar-img {
    width: 36px;
    height: 36px;
    border-radius: 50% !important;
    border: 2px solid var(--md-surface) !important;
    box-shadow: 0 0 0 1px var(--md-outline) !important;
}
.gauth-avatar-name {
    font-weight: 500;
    color: var(--md-on-surface);
}

/* Global Markdown Colors for Light Theme */
.stMarkdown {
    color: var(--md-on-background) !important;
}
"""

def inject_material3_theme():
    """
    Injects the Material Design 3 Light Theme CSS into the Streamlit app.
    This should be called exactly once near the top of app.py.
    """
    st.markdown(f"<style>{MATERIAL3_CSS}</style>", unsafe_allow_html=True)
