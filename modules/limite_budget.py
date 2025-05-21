import streamlit as st 
import pandas as pd
from models.email_engine import send_email
from datetime import datetime
from collections import defaultdict
from models.ui_utils import bouton_retour_accueil
from models.export_utils import telecharger_recapitulatif

def app():
    st.title("📥 Limite budget recherche")
    bouton_retour_accueil("retour_nouveau_fonds")

    try:
        df = pd.read_excel("BDD.xlsx", sheet_name="Fonds et Recherche")
    except Exception as e:
        st.error(f"Erreur de lecture du fichier BDD.xlsx : {e}")
        return

    asset_managers = sorted(df['Asset Manager'].dropna().unique())
    selected_am = st.selectbox("Sélectionnez un Asset Manager", asset_managers)

    if not selected_am:
        return

    for col in ["CSA EQ", "Recherche EQ", "CSA ALGO", "Recherche ALGO", "CSA ETF", "Recherche ETF"]:
        if col not in df.columns:
            df[col] = 0.0
        else:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)

    filtered_df = df[df['Asset Manager'] == selected_am]

    produit_mapping = {
        "Equities": ("CSA EQ", "Recherche EQ", "Mail Broker EQ"),
        "ALGO": ("CSA ALGO", "Recherche ALGO", "Mail Broker ALGO"),
        "ETF": ("CSA ETF", "Recherche ETF", "Mail Broker ETF")
    }

    email_map = defaultdict(lambda: {"produits": [], "brokers": set()})

    for _, row in filtered_df.iterrows():
        broker = row.get("Broker", "")
        for produit, (col_csa, col_rech, col_mail) in produit_mapping.items():
            csa = float(row.get(col_csa, 0))
            rech = float(row.get(col_rech, 0))
            if csa == 0 and rech == 0:
                continue
            emails = [e.strip() for e in str(row.get(col_mail, "")).split(";") if e.strip()]
            for email in emails:
                email_map[email]["produits"].append((produit, csa, rech))
                email_map[email]["brokers"].add(broker)

    if not email_map:
        st.info("✅ Aucun budget recherche à notifier pour cet Asset Manager.")
        return

    st.subheader("Paramètres de l'email")
    default_subject =  f"Limite budget de recherche {selected_am}"
    user_subject_template = st.text_input("Objet de l'email (modifiable)", value=default_subject)

    default_body = """
Bonjour,

{message_details}

Merci d'arrêter la collecte de recherche et CSA jusqu'à nouvel ordre.

Cordialement,

TRADING Exoé,
6, rue de Lisbonne,
75008 Paris,
Equities : +33(1) 80 20 65 41,
trading@exoe.fr,
Taux : +33(1) 80 20 65 70,
fixedincome@exoe.fr
www.exoe.fr
    """
    user_template = st.text_area("Modèle de message (modifiable)", value=default_body.strip(), height=300)

    if st.button("📄 Prévisualiser les emails"):
        previews = []

        for email, data in email_map.items():
            lignes = []
            produit_labels = []
            for produit, csa, rech in data["produits"]:
                produit_labels.append(produit)
                if csa > 0 and rech > 0:
                    lignes.append(f"• {produit} : CSA de {csa} bps et Recherche de {rech} bps")
                elif csa > 0:
                    lignes.append(f"• {produit} : CSA de {csa} bps")
                elif rech > 0:
                    lignes.append(f"• {produit} : Recherche de {rech} bps")

            broker_str = ", ".join(sorted(data["brokers"]))
            message_details = f"Nous vous informons que le budget recherche de {selected_am} pour {broker_str} a atteint sa limite sur les produits suivants :\n\n" + "\n".join(lignes)
            body = user_template.replace("{message_details}", message_details)
            subject = user_subject_template.replace("{asset_manager}", selected_am)

            previews.append({
                "broker": broker_str,
                "emails": email,
                "body": body,
                "subject": subject,
                "produit_str": ", ".join(sorted(set(produit_labels)))
            })

        st.session_state["previews"] = previews

    if "previews" in st.session_state:
        st.markdown("---")
        st.header("✉️ Prévisualisation des emails")

        for i, p in enumerate(st.session_state["previews"]):
            st.subheader(f"Broker : {p['broker']} | Produits : {p['produit_str']}")
            st.markdown(f"Destinataires : {email}")
            st.text_area("", value=p['body'], height=300, key=f"preview_{i}")

        if st.button("📨 Envoyer les emails"):
            historique = []
            for p in st.session_state["previews"]:
                send_email(
                    to_address=p['emails'],
                    subject=p['subject'],
                    body=p['body'],
                    attachments=[]
                )
                historique.append({
                    "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Broker": p['broker'],
                    "Instrument": p['produit_str'],
                    "Adresse Email": p['emails'],
                    "Statut": "Envoyé"
                })

            st.session_state["suivi_envois"] = historique
            st.success("✅ Tous les emails ont été envoyés.")

    if st.session_state.get("suivi_envois"):
        st.markdown("---")
        telecharger_recapitulatif(st.session_state["suivi_envois"])