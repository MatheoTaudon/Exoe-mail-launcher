import streamlit as st
import pandas as pd
from datetime import datetime
from models.email_engine import generate_preview_emails, send_email
from models.ui_utils import bouton_retour_accueil
from models.export_utils import telecharger_recapitulatif

def app():
    df_bdd = pd.read_excel("BDD.xlsx", sheet_name="Fonds et Recherche")
    asset_managers = sorted(set(df_bdd['Asset Manager'].dropna().unique()))

    st.title("📥 Enregistrement nouveau fonds")
    bouton_retour_accueil("retour_nouveau_fonds")

    if "preview_clicked" not in st.session_state:
        st.session_state["preview_clicked"] = False
    if "uploaded_files" not in st.session_state:
        st.session_state["uploaded_files"] = []
    if "suivi_envois" not in st.session_state:
        st.session_state["suivi_envois"] = []

    with st.form("email_form"):
        asset_manager = st.selectbox("Asset manager", asset_managers)

        st.markdown("**Produits à activer**")
        use_eq = st.checkbox("Equities")
        use_etf = st.checkbox("ETF")
        use_algo = st.checkbox("ALGO")
        use_deriv = st.checkbox("Derivatives")
        use_fi_cash = st.checkbox("Fixed Income (cash only)")
        use_fi_otc = st.checkbox("Fixed Income (OTC Derivatives)")
        use_fx_spot = st.checkbox("Forex (Spot only)")
        use_fx_full = st.checkbox("Forex (Spot et Forward)")
        use_convert = st.checkbox("Convertible")

        selected_products = []
        if use_eq: selected_products.append("Equities")
        if use_etf: selected_products.append("ETF")
        if use_algo: selected_products.append("ALGO")
        if use_deriv: selected_products.append("Derivatives")
        if use_fi_cash: selected_products.append("FI_CASH")
        if use_fi_otc: selected_products.append("FI_OTC")
        if use_fx_spot: selected_products.append("FX_SPOT")
        if use_fx_full: selected_products.append("FX_FULL")
        if use_convert: selected_products.append("CONVERT")

        st.markdown("**Informations sur le fonds**")
        fund_name = st.text_input("Fund name")
        lei = st.text_input("LEI")
        tag_name = st.text_input("TAG NAME (pour EQ, ETF, ALGO, Derivatives)")
        isda = st.text_input("ISDA (pour Derivatives, FI OTC, FX Spot/Forward)")

        contact_email = st.text_input("Contact email")
        email_subject = st.text_input("Email subject")

        uploaded_files = st.file_uploader("Attachments", accept_multiple_files=True)
        if uploaded_files:
            st.session_state["uploaded_files"] = uploaded_files

        if st.form_submit_button("📄 Prévisualiser les emails"):
            previews = generate_preview_emails(
                asset_manager=asset_manager,
                fund_name=fund_name,
                lei=lei,
                tag_name=tag_name,
                isda=isda,
                selected_products=selected_products,
                contact_email=contact_email,
                df=df_bdd
            )
            st.session_state["preview_clicked"] = True
            st.session_state["generated_emails"] = list(previews.keys())

            for email, data in previews.items():
                st.session_state[f"body_{email}"] = data["body"]
                st.session_state[f"products_{email}"] = data["products"]
                st.session_state[f"broker_{email}"] = data["broker"]

    if st.session_state.get("preview_clicked") and "generated_emails" in st.session_state:
        st.markdown("---")
        st.header("✉️ Prévisualisation des emails")

        for i, email in enumerate(st.session_state["generated_emails"]):
            broker = st.session_state.get(f"broker_{email}", email)
            prods = st.session_state.get(f"products_{email}", [])
            body = st.session_state.get(f"body_{email}", "")
            st.subheader(f"Broker : {broker} | Produits : {', '.join(prods)}")
            st.markdown(f"Destinataires : {email}")
            st.text_area("", value=body, height=300, key=f"preview_{i}")

        if st.button("📤 Envoyer les emails"):
            attachments = st.session_state.get("uploaded_files", [])
            if not attachments:
                st.error("❌ Merci d’ajouter au moins une pièce jointe avant d’envoyer.")
            else:
                for email in st.session_state["generated_emails"]:
                    body = st.session_state.get(f"body_{email}", "")
                    send_email(
                        to_address=email,
                        subject=email_subject,
                        body=body,
                        attachments=attachments
                    )
                    st.success(f"✅ Email envoyé à {email}")
                    st.session_state["suivi_envois"].append({
                        "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Broker": st.session_state.get(f"broker_{email}", ""),
                        "Instrument": ", ".join(st.session_state.get(f"products_{email}", [])),
                        "Adresse Email": email,
                        "Statut": "Envoyé"
                    })

    if st.session_state.get("suivi_envois"):
        st.markdown("---")
        telecharger_recapitulatif(st.session_state["suivi_envois"])