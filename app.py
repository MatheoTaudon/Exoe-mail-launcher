import streamlit as st
from modules import accueil, nouveau_fonds, limite_budget, changement_commissions

st.set_page_config(layout="wide", page_title="Exoé", page_icon="📊")

# Liste des pages
PAGES = {
    "Accueil": accueil.app,
    "Nouveau Fonds": nouveau_fonds.app,
    "Limite Budget Recherche": limite_budget.app,
    "Changement Commissions": changement_commissions.app,
}

# Initialisation
if "nav_page" not in st.session_state:
    st.session_state["nav_page"] = "Accueil"

# Affichage de la page active
PAGES[st.session_state["nav_page"]]()