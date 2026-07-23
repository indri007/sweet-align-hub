"""
pages/ — one module per wizard step (A-E) of the JobMatch AI app.

Each module exposes a single render_step_x(navigate) function that
draws that step's UI and handles its own session_state.

NOTE: this is a plain Python package for internal app organization,
not Streamlit's native multipage `pages/` auto-routing folder. Since
app.py still controls navigation via st.session_state.current_step,
Streamlit will NOT treat these as separate auto-routed pages.
"""
