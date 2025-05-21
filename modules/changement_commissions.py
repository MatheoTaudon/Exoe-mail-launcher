import streamlit as st
import pandas as pd
from collections import defaultdict
from models.email_engine import send_email
from models.ui_utils import bouton_retour_accueil
from models.export_utils import telecharger_recapitulatif
from datetime import datetime

def app():
    st.title("📥 Changement de commissions")
    bouton_retour_accueil("retour_nouveau_fonds")

    try:
        df = pd.read_excel("BDD.xlsx", sheet_name="Changement commissions")
    except Exception as e:
        st.error(f"Erreur de lecture de la feuille 'Changement commissions' : {e}")
        return

    df = df.fillna(0)
    if "suivi_envois" not in st.session_state:
        st.session_state["suivi_envois"] = []

    st.subheader("Sélection du client")
    asset_managers = sorted(df['Asset Manager'].dropna().unique())
    selected_am = st.selectbox("Asset Manager", asset_managers)

    filtered_am = df[df['Asset Manager'] == selected_am]

    all_funds = sorted(filtered_am['Fonds'].unique())
    fund_options = ["-- Tous les fonds --"] + all_funds
    selected_funds_raw = st.multiselect("Fonds", fund_options)
    selected_funds = all_funds if "-- Tous les fonds --" in selected_funds_raw else selected_funds_raw

    filtered_funds = filtered_am[filtered_am['Fonds'].isin(selected_funds)]

    all_brokers = sorted(filtered_funds['Broker'].unique())
    broker_options = ["-- Tous les brokers --"] + all_brokers
    selected_brokers_raw = st.multiselect("Brokers", broker_options)
    selected_brokers = all_brokers if "-- Tous les brokers --" in selected_brokers_raw else selected_brokers_raw

    final_df = filtered_funds[filtered_funds['Broker'].isin(selected_brokers)]

    st.subheader("Produits concernés")
    products = {
        "Equities": "Mail Broker EQ",
        "ETFs": "Mail Broker ETFs",
        "ALGO": "Mail Broker ALGO"
    }

    selected_products = [p for p in products if st.checkbox(p)]

    st.subheader("Objet de l'email")
    default_subject = f"Changement commissions {selected_am}"
    user_subject = st.text_input("Objet de l'email", value=default_subject)

    st.subheader("Nouvelles commissions à appliquer")
    commissions = {}
    for product in selected_products:
        st.markdown(f"**{product}**")
        commissions[product] = {
            "EXOE": st.number_input(f"EXOE ({product})", min_value=0.0, format="%.2f", key=f"exoe_{product}"),
            "EXEC": st.number_input(f"Broker Execution ({product})", min_value=0.0, format="%.2f", key=f"exec_{product}"),
            "CSA": st.number_input(f"CSA ({product})", min_value=0.0, format="%.2f", key=f"csa_{product}"),
            "RECH": st.number_input(f"Recherche ({product})", min_value=0.0, format="%.2f", key=f"rech_{product}"),
        }

    if st.button("📄 Prévisualiser les emails"):
        email_map = defaultdict(lambda: {"products": defaultdict(list), "brokers": set()})

        for _, row in final_df.iterrows():
            broker = row['Broker']
            for product in selected_products:
                col_mail = products[product]
                if col_mail in row and pd.notna(row[col_mail]):
                    emails = [e.strip() for e in str(row[col_mail]).split(";") if e.strip()]
                    for email in emails:
                        email_map[email]["products"][product].append(row['Fonds'])
                        email_map[email]["brokers"].add(broker)

        st.session_state["email_bodies"] = {}

        for email, data in email_map.items():
            lines = [
                f"Bonjour,\n",
                f"Merci de bien vouloir appliquer dès demain les taux de commissions suivants pour le client {selected_am} :"
            ]

            for product in data["products"]:
                com = commissions[product]
                fonds_list = data["products"][product]
                lines.append(f"\n{product}")
                for f in fonds_list:
                    total = com['EXOE'] + com['EXEC'] + com['CSA'] + com['RECH']
                    line = (
                        f"• {f} :\n"
                        f"EXOÉ : {com['EXOE']} bps – Exécution broker : {com['EXEC']} bps – "
                        f"CSA : {com['CSA']} bps – Recherche : {com['RECH']} bps – Total : {total:.1f} bps"
                    )
                    lines.append(line)

            lines.append(
                "\nBien cordialement,\n\n"
                "TRADING Exoé\n"
                "6, rue de Lisbonne\n"
                "75008 Paris\n"
                "Equities : +33(1) 80 20 65 41\n"
                "trading@exoe.fr\n"
                "Taux : +33(1) 80 20 65 70\n"
                "fixedincome@exoe.fr\n"
                "www.exoe.fr"
            )

            full_body = "\n".join(lines)
            st.session_state["email_bodies"][email] = {
                "recipients": email,
                "body": full_body,
                "subject": user_subject,
                "broker": ", ".join(data["brokers"]),
                "products": ", ".join(data["products"].keys())
            }

    if "email_bodies" in st.session_state:
        st.markdown("---")
        st.header("✉️ Prévisualisation des emails")
        for email, info in st.session_state["email_bodies"].items():
            st.subheader(f"Broker : {info['broker']} | Produits : {info['products']}")
            st.markdown(f"Destinataires : {email}")
            st.text_area("Contenu de l'email", value=info['body'], height=300, key=email)

        if st.button("📨 Envoyer les emails"):
            for email, info in st.session_state["email_bodies"].items():
                send_email(
                    to_address=email,
                    subject=info['subject'],
                    body=info['body'],
                    attachments=[]
                )
                st.session_state["suivi_envois"].append({
                    "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Broker": info['broker'],
                    "Instrument": info['products'],
                    "Adresse Email": email,
                    "Statut": "Envoyé"
                })

            st.success("✅ Tous les emails ont été envoyés.")

    if st.session_state.get("suivi_envois"):
        st.markdown("---")
        telecharger_recapitulatif(st.session_state["suivi_envois"])
