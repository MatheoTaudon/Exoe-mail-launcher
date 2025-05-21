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

    if "suivi_envois" not in st.session_state:
        st.session_state["suivi_envois"] = []

    # Sélection du client
    st.subheader("Sélection du client")
    asset_managers = sorted(df['Asset Manager'].dropna().unique())
    selected_am = st.selectbox("Asset Manager", asset_managers)
    filtered_am = df[df['Asset Manager'] == selected_am]

    # Sélection des brokers
    all_brokers = sorted(filtered_am['Broker'].dropna().unique())
    broker_options = ["-- Tous les brokers --"] + all_brokers
    selected_brokers_raw = st.multiselect("Brokers", broker_options)
    selected_brokers = all_brokers if "-- Tous les brokers --" in selected_brokers_raw else selected_brokers_raw
    final_df = filtered_am[filtered_am['Broker'].isin(selected_brokers)]

    # Produits concernés
    st.subheader("Produits concernés")
    products = {
        "Equities": ("CSA EQ", "Recherche EQ", "Mail Broker EQ"),
        "ALGO": ("CSA ALGO", "Recherche ALGO", "Mail Broker ALGO"),
        "ETF": ("CSA ETF", "Recherche ETF", "Mail Broker ETF")
    }
    selected_products = [p for p in products if st.checkbox(p)]

    if not selected_products:
        st.warning("Veuillez sélectionner au moins un produit.")
        return

    email_map = defaultdict(lambda: {"products": defaultdict(list), "brokers": set()})

    for _, row in final_df.iterrows():
        broker = row.get("Broker", "")
        for product in selected_products:
            csa_col, rech_col, mail_col = products[product]
            csa = float(row.get(csa_col, 0))
            rech = float(row.get(rech_col, 0))
            if csa == 0 and rech == 0:
                continue
            emails = [e.strip() for e in str(row.get(mail_col, "")).split(";") if e.strip()]
            for email in emails:
                email_map[email]["products"][product].append((broker, csa, rech))
                email_map[email]["brokers"].add(broker)

    if not email_map:
        st.info("✅ Aucun budget recherche à notifier avec les filtres sélectionnés.")
        return

    st.subheader("Objet de l'email")
    default_subject = f"Limite budget de recherche {selected_am}"
    user_subject = st.text_input("Objet de l'email", value=default_subject)

    if st.button("📄 Prévisualiser les emails"):
        previews = []

        for email, data in email_map.items():
            lignes = []
            produit_labels = []
            for product, values in data["products"].items():
                produit_labels.append(product)
                lignes.append(f"\n{product}")
                for broker, csa, rech in values:
                    if csa > 0 and rech > 0:
                        lignes.append(f"• {broker} : CSA de {csa} bps et Recherche de {rech} bps")
                    elif csa > 0:
                        lignes.append(f"• {broker} : CSA de {csa} bps")
                    elif rech > 0:
                        lignes.append(f"• {broker} : Recherche de {rech} bps")

            broker_str = ", ".join(sorted(data["brokers"]))
            message = "\n".join([
                "Bonjour,\n",
                f"Nous vous informons que le budget recherche de {selected_am} pour {broker_str} a atteint sa limite sur les produits suivants :",
                "\n".join(lignes),
                "\nMerci d'arrêter la collecte de recherche et CSA jusqu'à nouvel ordre.\n",
                "Cordialement,\n\n",
                "TRADING Exoé",
                "6, rue de Lisbonne",
                "75008 Paris",
                "Equities : +33(1) 80 20 65 41",
                "trading@exoe.fr",
                "Taux : +33(1) 80 20 65 70",
                "fixedincome@exoe.fr",
                "www.exoe.fr"
            ])

            previews.append({
                "broker": broker_str,
                "emails": email,
                "body": message,
                "subject": user_subject,
                "produit_str": ", ".join(sorted(set(produit_labels)))
            })

        st.session_state["previews"] = previews

    if "previews" in st.session_state:
        st.markdown("---")
        st.header("✉️ Prévisualisation des emails")

        for i, p in enumerate(st.session_state["previews"]):
            st.subheader(f"Broker : {p['broker']} | Produits : {p['produit_str']}")
            st.markdown(f"Destinataires : {p['emails']}")
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

    if st.session_state.get("suivi_envois"):
        st.markdown("---")
        telecharger_recapitulatif(st.session_state["suivi_envois"])
