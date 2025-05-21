import streamlit as st

def app():
    # Afficher le logo avec st.image (fonctionne avec un fichier local)
    col1, col2, col3 = st.columns([1, 0.65, 0.7])
    with col2:
        st.image("logo.png", width=300)

    # Centrage des boutons
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
            <style>
                div.stButton > button {
                    width: 100%; 
                    padding: 1rem;
                    font-size: 20px;
                    margin-bottom: 1rem;
                    border-radius: 10px;
                }
            </style>
        """, unsafe_allow_html=True)

        if st.button("Enregistrer un nouveau fonds"):
            st.session_state["nav_page"] = "Nouveau Fonds"
            st.rerun()

        if st.button("Limite budget recherche atteinte"):
            st.session_state["nav_page"] = "Limite Budget Recherche"
            st.rerun()

        if st.button("Effectuer un changement de commissions"):
            st.session_state["nav_page"] = "Changement Commissions"
            st.rerun()

      