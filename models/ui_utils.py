import streamlit as st

def bouton_retour_accueil(key):
    """
    Affiche un bouton en haut à gauche pour revenir à l'accueil.
    Le paramètre `key` permet de rendre le bouton unique par page.
    """
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("⬅️ Accueil", key=key):
            st.session_state["nav_page"] = "Accueil"
            st.rerun()