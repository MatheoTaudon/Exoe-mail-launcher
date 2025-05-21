import pandas as pd
import smtplib
from email.message import EmailMessage
import re
import streamlit as st

def send_email(to_address, subject, body, attachments):
    recipients_raw = [email.strip() for email in to_address.split(';') if email.strip()]
    recipients = [email for email in recipients_raw if '@' in email and '.' in email]

    if not recipients:
        st.warning(f"❌ Aucun email valide trouvé parmi : {to_address}")
        return

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = "taudonm@gmail.com"
    msg['To'] = ', '.join(recipients)
    msg.set_content(body)

    for file in attachments:
        content = file.read()
        msg.add_attachment(content, maintype='application', subtype='octet-stream', filename=file.name)

    with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
        smtp.starttls()
        smtp.login('taudonm@gmail.com', 'bftd uvww apbv vbzl')
        smtp.send_message(msg)


def generate_preview_emails(asset_manager, fund_name, lei, tag_name, isda,
                            selected_products, contact_email, df):
    mail_columns = {
        "Equities": "Mail Broker EQ",
        "ETF": "Mail Broker ETF",
        "ALGO": "Mail Broker ALGO",
        "Derivatives": "Mail Broker dérivés",
        "FI_CASH": "Mail Broker FI",
        "FI_OTC": "Mail Broker FI",
        "FX_SPOT": "Mail Broker FX",
        "FX_FULL": "Mail Broker FX",
        "CONVERT": "Mail Broker Convert"
    }

    commission_columns = {
        "Equities": ("Exoe com EQ", "Broker com EQ", "CSA EQ"),
        "ETF": ("Exoe com ETF", "Broker com ETF", "CSA ETF"),
        "ALGO": ("Exoe com ALGO", "Broker com ALGO", "CSA ALGO")
    }

    instruments_labels = {
        "Equities": "Equities",
        "ETF": "ETFs",
        "ALGO": "Equities by ALGO",
        "Derivatives": "Derivatives",
        "FI_CASH": "Fixed Income (cash only)",
        "FI_OTC": "Fixed Income (OTC Derivatives)",
        "FX_SPOT": "Forex (Spot only)",
        "FX_FULL": "Forex (Spot & Forward)",
        "CONVERT": "Convertible Bonds"
    }

    tag_name_required = {"Equities", "ETF", "ALGO", "Derivatives"}
    isda_required = {"Derivatives", "FI_OTC", "FX_FULL"}

    email_map = {}

    for _, row in df[df["Asset Manager"] == asset_manager].iterrows():
        broker = row.get("Broker", "Unknown")
        for prod in selected_products:
            col_mail = mail_columns.get(prod)
            if not col_mail or pd.isna(row.get(col_mail)):
                continue
            emails = [e.strip() for e in str(row[col_mail]).split(';') if e.strip()]
            email_key = "; ".join(sorted(set(emails)))
            if email_key not in email_map:
                email_map[email_key] = {"products": [], "rows": [], "brokers": set()}
            email_map[email_key]["products"].append(prod)
            email_map[email_key]["rows"].append(row)
            email_map[email_key]["brokers"].add(broker)

    previews = {}
    for email, data in email_map.items():
        row = data["rows"][0]
        products = sorted(set(data["products"]))
        broker_name = ", ".join(sorted(data["brokers"]))

        # Introduction
        body_lines = [f"Hello,\n"]
        body_lines.append(f"{asset_manager} is launching a new fund: {fund_name}.")

        # Fichiers joints listés
        details = [f"the fund’s Prospectus, SSI, LEI ({lei})"]
        if any(p in tag_name_required for p in products) and tag_name:
            details.append(f"TAG NAME ({tag_name})")
        if any(p in isda_required for p in products) and isda:
            details.append(f"ISDA ({isda})")
        body_lines.append(f"Please find attached {', '.join(details)}.")

        # Liste des instruments
        instr_list = []
        for p in products:
            label = instruments_labels.get(p, p)
            instr_list.append(label)

        if instr_list:
            if len(instr_list) > 1:
                instr_text = ", ".join(instr_list[:-1]) + " and " + instr_list[-1]
            else:
                instr_text = instr_list[0]
            body_lines.append(f"The instruments traded will include {instr_text}.")

        # Détail des commissions
        if any(p in commission_columns for p in products):
            body_lines.append("\nHere are the commission details:")
            for p in products:
                if p in commission_columns:
                    exoe_col, bkr_col, csa_col = commission_columns[p]
                    exoe = float(row.get(exoe_col, 0))
                    bkr = float(row.get(bkr_col, 0))
                    csa = float(row.get(csa_col, 0))
                    total = exoe + bkr + csa
                    body_lines.append(f"\n{p}:")
                    body_lines.append(f"• Execution commission EXOE: {exoe} bps")
                    body_lines.append(f"• Execution commission Broker: {bkr} bps")
                    body_lines.append(f"• CSA commission: {csa} bps")
                    body_lines.append(f"• Total commission: {total} bps")

        # Contact + signature
        body_lines.append(f"\nFor any further information, feel free to contact: {contact_email}.")
        body_lines += ["", "Best regards,", "", "TRADING Exoé", "6, rue de Lisbonne", "75008 Paris",
                       "Equities :+33(1) 80 20 65 41", "trading@exoe.fr", "Taux : +33(1) 80 20 65 70",
                       "fixedincome@exoe.fr", "www.exoe.fr"]

        full_body = "\n".join(body_lines)

        previews[email] = {
            "body": full_body,
            "products": products,
            "broker": broker_name
        }

    return previews