import streamlit as st

st.set_page_config(
    page_title="Basket Tracker",
    layout="wide"
)

# =========================
# HEADER
# =========================

c1, c2 = st.columns(
    [1, 5]
)

with c1:

    st.image(
        "assets/logo.png",
        width=120
    )

with c2:

    st.title(
        "🏀 Basket Tracker"
    )

    st.markdown(
        "Sistema de seguimiento físico Cadete Femenino 2026"
    )